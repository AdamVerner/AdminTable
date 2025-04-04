import ast
import dataclasses
from collections.abc import Callable, Generator
from typing import Annotated, Any, Literal, cast

from sqlalchemy import BinaryExpression, ColumnElement, Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    ColumnProperty,
    DeclarativeBase,
    InstrumentedAttribute,
    Query,
    Session,
)
from sqlalchemy.orm.instrumentation import manager_of_class
from sqlalchemy.sql.functions import count
from typing_extensions import Doc

from admin_table.config import Resource
from admin_table.modules.bases import ResolvedData, ResolverBase

SQLAlchemyListView_FieldType = str | InstrumentedAttribute | Query | ColumnElement


class SQLAlchemyResolver(ResolverBase):
    model: type[DeclarativeBase]
    async_session_maker: Callable[[], AsyncSession] | None = None
    session_maker: Callable[[], Session] | None = None

    def __init__(
        self,
        session: Annotated[
            Callable[[], Session | AsyncSession],
            Doc("Function called at runtime which should provide a session"),
        ],
        model: Annotated[type[DeclarativeBase], Doc("Base model from which the attributes will be selected")],
        extra_cols: Annotated[
            dict[str, Query | ColumnElement | InstrumentedAttribute] | None,
            Doc("Extra columns to be added to the list view"),
        ] = None,
    ):
        self.model = model
        self.extra_cols = extra_cols or {}
        if isinstance(session(), AsyncSession):
            self.async_session_maker = cast(Callable[[], AsyncSession], session)
        else:
            self.session_maker = cast(Callable[[], Session], session)

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

            if attr.property.deferred:
                print("Deffered, skipping", attr, attr.property)
                continue

            all_columns[name] = self.__ListColumns(ref=name, src=attr, sortable=True)

        # parse additional columns provided by the user
        for name, column in self.extra_cols.items():
            if isinstance(column, Query | ColumnElement | InstrumentedAttribute):
                all_columns[name] = self.__ListColumns(ref=name, src=column.label(name), sortable=False)

            else:
                raise ValueError(f"Invalid column type for {name}: {column}")

        assert all_columns, "No columns found in the model"
        assert all_columns.get(resource.id_col), "ID column not found in the model"

        return all_columns

    @staticmethod
    def __generate_filter_expression(
        attributes: dict[str, __ListColumns], filters: list[ResolverBase.AppliedFilter]
    ) -> Generator[BinaryExpression, None, None]:
        for f in filters:
            sql_column = attributes[f.ref].src

            if f.op == "is_null":
                yield sql_column.is_(None)
                continue

            if f.op == "is_not_null":
                yield sql_column.isnot(None)
                continue

            # convert value to the correct type
            if f.op == "in":
                value = ast.literal_eval(f.val or "[]")
                assert isinstance(value, list | tuple), f'Invalid value type "{value}", must be List'
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

    def _make_entity(self, entry: Row[tuple[Any]], attributes: dict[str, __ListColumns]) -> dict[str, str]:
        """Returns entity which can be used as both class and dict"""
        obj = {key: value for value, key in zip(entry, attributes.keys())}

        class ModelOverwrite(self.model):  # type: ignore[name-defined]
            __abstract__ = True

            def __getitem__(self, item):
                return obj[item]

            def get(self, *args, **kwargs):
                return obj.get(*args, **kwargs)

        entity = ModelOverwrite(**{k: v for k, v in obj.items() if k in dir(self.model)})
        # make_transient_to_detached(entity)
        return cast(dict[str, str], entity)

    async def resolve_list(
        self,
        resource: "Resource",
        page: int,
        per_page: int,
        filters: list[ResolverBase.AppliedFilter],
        sort: tuple[str, Literal["asc", "desc"]],
    ) -> ResolverBase.ResolvedListData:
        attributes = self.__resolve_model_attributes(resource)

        select_sort = getattr(attributes[sort[0]].src, sort[1])()
        filter_expressions = self.__generate_filter_expression(attributes, filters)

        # generate the query which will be executed
        base_select = select(*[col.src for col in attributes.values()]).filter(*filter_expressions)
        list_select = base_select.limit(per_page).offset((page - 1) * per_page).order_by(select_sort)

        # execute queries
        if self.async_session_maker:
            async with self.async_session_maker() as session:
                total = await session.scalar(select(count()).select_from(base_select.subquery()))
                rows = (await session.execute(list_select)).fetchall()
        elif self.session_maker:
            with self.session_maker() as session:
                total = session.execute(select(count()).select_from(base_select.subquery())).scalar()
                rows = session.execute(list_select).fetchall()
        else:
            raise RuntimeError("No session maker provided")

        list_data: list[dict[str, str]] = []

        for row in rows:
            entity = self._make_entity(row, attributes)
            list_data.append(cast(dict[str, str], entity))  # type: ignore

        # parse data into a dictionary
        return self.ResolvedListData(
            list_data=list_data,
            pagination={"page": page, "per_page": per_page, "total": total or 0},
        )

    async def resolve_detail(self, resource: "Resource", entry_id: str) -> ResolvedData | None:
        """Resolve data of a single entry"""
        attributes = self.__resolve_model_attributes(resource)
        assert resource.id_col in attributes, f'Model does not have id col: "{resource.id_col}'
        col_src: InstrumentedAttribute = attributes[resource.id_col].src
        casted_id = col_src.type.python_type(entry_id)

        base_select = select(*[col.src for col in attributes.values()]).filter(col_src == casted_id).limit(1)

        if self.async_session_maker:
            async with self.async_session_maker() as session:
                entry = (await session.execute(base_select)).first()
        elif self.session_maker:
            with self.session_maker() as session:
                entry = session.execute(base_select).first()
        else:
            raise RuntimeError("No session maker provided")

        if entry is None:
            return None

        entity = self._make_entity(entry, attributes)
        return entity  # type: ignore

    def get_filter_options(self, resource: "Resource") -> dict[str, ResolverBase.FilterOption]:
        all_columns = self.__resolve_model_attributes(resource)

        return {
            ref: ResolverBase.FilterOption(
                reference=ref,
                display=col.src.description or ref,
            )
            for ref, col in all_columns.items()
        }
