import abc
import dataclasses
from typing import TYPE_CHECKING, Annotated, List, Literal, Tuple, TypeAlias

from typing_extensions import Doc

if TYPE_CHECKING:
    from admin_table.config import Resource

ResolvedData: TypeAlias = dict[str, str]


class ResolverBase(abc.ABC):
    @dataclasses.dataclass
    class AppliedFilter:
        ref: str
        op: str
        val: str
        display: str = None

    @dataclasses.dataclass
    class ResolvedListData:
        list_data: Annotated[list[ResolvedData], Doc("List of all resolved data entries")]
        pagination: dict[Literal["page", "per_page", "total"], int]

    @abc.abstractmethod
    def resolve_list(
        self,
        resource: "Resource",
        page: int,
        per_page: int,
        filters: List[AppliedFilter],
        sort: Tuple[str, Literal["asc", "desc"]],
    ) -> ResolvedListData:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_detail(self, resource: "Resource", entry_id: str) -> ResolvedData:
        raise NotImplementedError()

    @dataclasses.dataclass
    class FilterOption:
        display: str
        reference: str

    @abc.abstractmethod
    def get_filter_options(self, resource: "Resource") -> dict[str, FilterOption]:
        """
        Returns a dictionary of filter options for the given view.
        each key is the reference of the filter and the value is the FilterOption object.
        """
        raise NotImplementedError()
