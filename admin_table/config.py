import dataclasses
import random
from typing import TYPE_CHECKING, Any, Callable, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.orm import InstrumentedAttribute
from typing_extensions import Annotated, Doc, Literal

if TYPE_CHECKING:
    from admin_table.modules.bases.list_resolver import ResolverBase


class DefaultAuthProvider:
    @dataclasses.dataclass
    class User:
        email: str
        name: str | None = None
        avatar: str | None = None

    def authenticate(self, username: str | None, password: str | None) -> User | Literal[False]:
        if username == "admin@admin.admin" and password == "admin@admin.admin":
            return self.User(
                email="admin@admin.admin",
                name="Admin",
                avatar=f"https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/avatars/"
                f"avatar-{random.randrange(0, 10)}.png",
            )
        return False

    def generate_token(self, user: User) -> str:
        """Generate secure token for the user"""
        assert isinstance(user, self.User)
        return user.email

    def validate_token(self, token: str) -> User | Literal[False]:
        if token == "admin@admin.admin":
            return self.User(
                email="admin@admin.admin",
                name="Admin",
                avatar=f"https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/avatars/"
                f"avatar-{random.randrange(0, 10)}.png",
            )
        return False


@dataclasses.dataclass
class AdminTableConfig:
    name: Annotated[str, Doc("The name of the AdminTable")] = "AdminTable"
    auth_provider: DefaultAuthProvider = dataclasses.field(default_factory=DefaultAuthProvider)
    dashboard: Annotated[
        Callable[[DefaultAuthProvider.User], str], Doc("Function generating the dashboard content")
    ] = dataclasses.field(default=lambda u: f"# Dashboard\n\nWelcome {u.email} to AdminTable")
    resources: List["Resource"] = dataclasses.field(default_factory=list)
    pages: List["Page"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Navigable:
    name: Annotated[str, Doc("Unique name of the resource")]
    navigation: Annotated[
        Optional[str],
        Doc(
            """
            Navigation drawer name. If not specified, resource will not be displayed in the navigation drawer.
            """
        ),
    ]
    display: Annotated[Optional[str], Doc("Name which will be displayed in the UI, defaults to name")] = None


@dataclasses.dataclass(kw_only=True)
class Resource(Navigable):
    views: Annotated["ResourceViews", Doc("Resource views")]
    resolver: Annotated["ResolverBase", Doc("Resolver for the list view")]
    id_col: Annotated[str, Doc("Column to be used as the id column")] = "id"


@dataclasses.dataclass(kw_only=True)
class Page(Navigable):
    content: Annotated[str | Callable[..., str], Doc("static content of function generating content")]
    type: Annotated[Literal["html", "markdown"], Doc("Type of the content")] = "markdown"


@dataclasses.dataclass
class ResourceViews:
    """Set of view for a resource"""

    list: Annotated[Optional["ListView"], Doc("List view")] = None
    create: Annotated[Optional["CreateView"], Doc("Create view")] = None
    detail: Annotated[Optional["DetailView"], Doc("Detail view")] = None


@dataclasses.dataclass
class ViewBase:
    title: Annotated[Optional[str], Doc("Title of the view")] = None
    description: Annotated[
        Callable[..., str] | str | None,
        Doc("Function generating description of the resource or the description itself"),
    ] = dataclasses.field(kw_only=True, default=None)


@dataclasses.dataclass
class LinkDetail:
    """Link to another entity"""

    """ref to be used to resolve the displayed value"""
    ref: str

    """name of the resource"""
    resource: str

    """column to get resource id from"""
    id_ref: str


@dataclasses.dataclass
class LinkTable:
    """Link to another entity"""

    """ref to be used to resolve the displayed value"""
    ref: str

    """name of the resource"""
    resource: str

    filter_col: str
    filter_op: Literal["eq", "like", "ilike", "in"]
    filter_ref: str  # column to get filter value from


"""
Type for field definitions
  - str: provided string is used as the column name and to resolve the column from the model
  - Column: attribute key is used to resolve the column from the model
  - InstrumentedAttribute: attribute key is used to resolve the column from the model
  - [str, str]: column name, ref which is resolved from the model
  - [str, Column]: column name, attribute from which key is used to resolve the column from the model
  - [str, InstrumentedAttribute]: column name, attribute from which key is used to resolve the column from the model
  - [str, LinkEntity]: column name, link to another entity
  - [str, LinkTable]: column name, link to another table
  - [str, str, str]: same as two-tuples, but with second item being a description
"""
ResolvableFieldType = str | Column | InstrumentedAttribute | LinkDetail | LinkTable | Callable[[Any], Any]
FieldName = str
FieldDescription = str
ListViewFieldType = (
    str
    | Column
    | InstrumentedAttribute
    | Tuple[FieldName, ResolvableFieldType]
    | Tuple[FieldName, FieldDescription, ResolvableFieldType]
)


@dataclasses.dataclass(kw_only=True)
class ListView(ViewBase):
    fields: Annotated[list[ListViewFieldType], Doc("List of fields to be selected from the model")]
    detail_value_ref: Annotated[Optional[str], Doc("Column to be used as the detail value")] = None

    filter_processor: Annotated[
        Optional[Callable[["ResolverBase.AppliedFilter"], "ResolverBase.AppliedFilter"]],
        Doc("Function processing the filter before passing it to the resolver"),
    ] = None


CreateSchemaModel = TypeVar("CreateSchemaModel", bound=BaseModel)


@dataclasses.dataclass(kw_only=True)
class CreateView(ViewBase, Generic[CreateSchemaModel]):
    schema: type[CreateSchemaModel]
    callback: Callable[[CreateSchemaModel], Any]


@dataclasses.dataclass
class SubTable:
    """Link to another entity"""

    """Displayed title"""
    title: str

    """name of the target resource"""
    resource: str

    filter_col: str
    filter_op: Literal["eq", "like", "ilike", "in"]
    filter_ref: str  # column to get filter value from

    description: str = ""


@dataclasses.dataclass(kw_only=True)
class DetailView(ViewBase):
    fields: Annotated[list[ListViewFieldType], Doc("List of fields to be selected from the model")]
    actions: Annotated[
        List[Callable[..., Any]],
        Doc(
            "List of actions to be added to the view."
            "Name and description of the action is taken from the functions __name__ and __doc__"
            "Fields are resolved automatically"
        ),
    ] = dataclasses.field(default_factory=list)
    tables: Annotated[
        List[SubTable],
        Doc(
            "List of tables to be added to the view."
            "The 'ref' is used as title name of the table instead of the resource name."
        ),
    ] = dataclasses.field(default_factory=list)
