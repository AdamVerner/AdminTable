import abc
import dataclasses
import random
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Generic, List, Optional, Protocol, Tuple, TypeVar

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
    icon_src: Annotated[str | None, Doc("Icon to be displayed in the navigation drawer")] = None
    version: Annotated[str | None, Doc("Current version of your application")] = None
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
    hidden: Annotated[bool, Doc("If the resource should be hidden from the navigation")] = False


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
  
if the value starts with prefix [[markdown]] or [[html]] it will be rendered as such...
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

    default_sort: Annotated[
        Tuple[str, str],
        Doc(
            "Default sorting column and direction. Column name is used to resolve the column from the model."
            "Direction is either 'asc' or 'desc', if no value is provided, the detail ref is used as default."
        ),
    ] = (None, "asc")

    hidden_filters: Annotated[
        Optional[list["ResolverBase.AppliedFilter"]],
        Doc(
            "Always-on set of filter which will NOT be displayed to the user."
            "These filters are not passed to the filter_processor and are applied directly to the query."
        ),
    ] = None
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


@dataclasses.dataclass
class GraphData(abc.ABC):
    chart_type: str


@dataclasses.dataclass(kw_only=True)
class LineGraphData(GraphData):
    """
    parameters corresponding to the recharts LineChart component in Mantine
    https://mantine.dev/charts/line-chart/?t=props
    """

    chart_type: str = "line"

    data: list[dict[str, Any]]  # Data used to display chart
    series: list[
        dict[str, Any]
    ]  # An array of objects with name and color keys. Determines which data should be consumed from the data array
    dataKey: str  # Key of the data object for x-axis values

    curveType: Literal["bump", "linear", "natural", "monotone", "step", "stepBefore", "stepAfter"] | None = (
        None  # Type of the curve, 'monotone' by default
    )
    connectNulls: bool | None = None  # Connect null values with a line
    fillOpacity: float | None = None  # Controls fill opacity of all lines, 1 by default
    gradientStops: list[dict[str, Any]] | None = None  # Data used to generate gradient stops
    gridAxis: Literal["none", "x", "y", "xy"] | None = (
        None  # Specifies which lines should be displayed in the grid, 'x' by default
    )
    gridProps: dict[str, Any] | None = None  # Props passed down to the CartesianGrid component
    legendProps: dict[str, Any] | None = None  # Props passed down to the Legend component
    lineChartProps: dict[str, Any] | None = None  # Props passed down to recharts LineChart component
    rightYAxisLabel: str | None = None  # A label to display next to the right y-axis
    rightYAxisProps: dict[str, Any] | None = None
    tickLine: Literal["none", "x", "y", "xy"] | None = (
        None  # Specifies which axis should have tick line, 'y' by default
    )
    type: Literal["default", "gradient"] | None = None  # Type of the chart, 'line' by default
    unit: str | None = None  # Unit displayed next to each tick in y-axis
    withDots: bool | None = None  # Determines whether dots should be displayed, true by default
    withLegend: bool | None = True  # Determines whether chart legend should be displayed, false by default
    withPointLabels: bool | None = None  # Determines whether each point should have associated label, false by default
    xAxisLabel: str | None = None  # A label to display below the x-axis
    yAxisLabel: str | None = None  # A label to display next to the y-axis


class GetGraphCallback(Protocol):
    __name__: str

    def __call__(
        self, __model: Any, range_from: Optional[datetime] = None, range_to: Optional[datetime] = None
    ) -> GraphData: ...


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
    graphs: Annotated[
        List[GetGraphCallback],
        Doc(
            "List of graphs to be added to the view."
            "Name and description of the graph is taken from the functions __name__ and __doc__"
            "The first parameter of the function is the data model from the resolver"
        ),
    ] = dataclasses.field(default_factory=list)
