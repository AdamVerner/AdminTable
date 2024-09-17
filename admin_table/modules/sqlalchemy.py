import ast
import dataclasses
from typing import Any, Callable, List, Literal, Optional, Tuple, Type, Union

from sqlalchemy import BinaryExpression, ColumnElement, select
from sqlalchemy.orm import (
    ColumnProperty,
    DeclarativeBase,
    InstrumentedAttribute,
    Query,
    Session,
    make_transient_to_detached,
)
from sqlalchemy.orm.instrumentation import manager_of_class
from sqlalchemy.sql.functions import count
from typing_extensions import Annotated, Doc

from admin_table.config import Resource
from admin_table.modules.bases.list_resolver import ResolvedData, ResolverBase

SQLAlchemyListView_FieldType = Union[str, InstrumentedAttribute, Query, ColumnElement]


class SQLAlchemyResolver(ResolverBase):
    def __init__(
        self,
        session: Annotated[Callable[[], Session], Doc("Function called at runtime which should provide a session")],
        model: Annotated[Type[DeclarativeBase], Doc("Base model from which the attributes will be selected")],
        extra_cols: Annotated[
            Optional[dict[str, Callable[[Any], str] | Query | ColumnElement]],
            Doc("Extra columns to be added to the list view"),
        ] = None,
    ):
        self.session_maker = session
        self.model = model
        self.extra_cols = extra_cols or {}

    @dataclasses.dataclass
    class __ListColumns:
        ref: str
        src: Any
        sortable: bool = False

    def __resolve_model_attributes(self, resource: "Resource") -> dict[str, __ListColumns]:
        """Generates a dictionary of all columns which can be used within the model"""
        manager = manager_of_class(self.model)
        # noinspection PyProtectedMember,PyTypeChecker
        all_keys: frozenset = manager._all_key_set

        all_columns = {}

        for name in all_keys:
            attr = getattr(self.model, name)

            # do not include instrumented attributes and other nonsense
            if not isinstance(attr.property, ColumnProperty):
                continue

            all_columns[name] = self.__ListColumns(ref=name, src=attr, sortable=True)

        # parse additional columns provided by the user
        for name, column in self.extra_cols.items():
            if isinstance(column, (Query, ColumnElement)):
                all_columns[name] = self.__ListColumns(ref=name, src=column.label(name), sortable=False)

        assert all_columns, "No columns found in the model"
        assert all_columns.get(resource.id_col), "ID column not found in the model"

        return all_columns

    @staticmethod
    def __generate_filter_expression(
        attributes: dict[str, __ListColumns], filters: List[ResolverBase.AppliedFilter]
    ) -> List[BinaryExpression]:
        for f in filters:
            sql_column = attributes.get(f.ref).src

            # convert value to the correct type
            if f.op == "in":
                value = ast.literal_eval(f.val or "[]")
                assert isinstance(value, (list, tuple)), f'Invalid value type "{value}", must be List'
                value = [sql_column.expression.type.python_type(x) for x in value]
            else:
                value = sql_column.expression.type.python_type(f.val)

            if (f.op == "like" or f.op == "ilike") and "%" not in value:
                value = f"%{value}%"

            if hasattr(sql_column, f.op):
                op = getattr(sql_column, f.op)
            elif hasattr(sql_column, f"__{f.op}__"):
                op = getattr(sql_column, f"__{f.op}__")
            else:
                raise AttributeError(f"Column {f.ref} does not support operation {f.op}")

            yield op(value)

    def resolve_list(
        self,
        resource: "Resource",
        page: int,
        per_page: int,
        filters: List[ResolverBase.AppliedFilter],
        sort: Tuple[str, Literal["asc", "desc"]],
    ) -> ResolverBase.ResolvedListData:
        attributes = self.__resolve_model_attributes(resource)

        select_sort = getattr(attributes[sort[0]].src, sort[1])()
        filter_expressions = self.__generate_filter_expression(attributes, filters)

        # generate the query which will be executed
        base_select = select(*[col.src for col in attributes.values()]).filter(*filter_expressions)
        list_select = base_select.limit(per_page).offset((page - 1) * per_page).order_by(select_sort)

        # execute queries
        with self.session_maker() as session:
            total = session.execute(select(count()).select_from(base_select)).scalar()
            rows = session.execute(list_select).fetchall()

        # parse data into a dictionary
        return self.ResolvedListData(
            list_data=[{key: value for value, key in zip(row, attributes.keys())} for row in rows],
            pagination={"page": page, "per_page": per_page, "total": total},
        )

    def resolve_detail(self, resource: "Resource", entry_id: str) -> ResolvedData:
        """Resolve data of a single entry"""
        attributes = self.__resolve_model_attributes(resource)
        assert resource.id_col in attributes, f'Model does not have id col: "{resource.id_col}'
        col_src: InstrumentedAttribute = attributes[resource.id_col].src
        casted_id = col_src.type.python_type(entry_id)

        base_select = select(*[col.src for col in attributes.values()]).filter(casted_id == col_src)

        with self.session_maker() as session:
            entry = session.execute(base_select).one()

        obj = {key: value for value, key in zip(entry, attributes.keys())}

        self.model.__getitem__ = lambda self, item: obj[item]
        self.model.get = lambda self, *args, **kwargs: obj.get(*args, **kwargs)

        entity = self.model(**{k: v for k, v in obj.items() if k in dir(self.model)})
        make_transient_to_detached(entity)
        # entity = session.merge(entity, load=False)

        # noinspection PyTypeChecker
        return entity

    def get_filter_options(self, resource: "Resource") -> dict[str, ResolverBase.FilterOption]:
        all_columns = self.__resolve_model_attributes(resource)

        return {
            ref: ResolverBase.FilterOption(
                reference=ref,
                display=col.src.description or ref,
            )
            for ref, col in all_columns.items()
        }
