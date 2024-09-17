import dataclasses
import logging
import os.path
import string
import sys
from inspect import Parameter, signature
from typing import Any, Callable, List, Literal, Tuple, cast
from urllib.parse import quote, unquote

from sqlalchemy.orm import InstrumentedAttribute
from starlette.datastructures import ImmutableMultiDict

from .config import (
    AdminTableConfig,
    CreateView,
    DefaultAuthProvider,
    DetailView,
    LinkDetail,
    LinkTable,
    ListView,
    Resource,
)
from .modules.bases.list_resolver import ResolverBase


@dataclasses.dataclass
class AdminTableRoute:
    @dataclasses.dataclass
    class RouteRequest:
        @dataclasses.dataclass
        class URL:
            scheme: str
            host: str
            port: int
            path: str
            query: str

        url: URL
        path_params: dict[str, str] = dataclasses.field(default_factory=lambda: {})
        query_params: ImmutableMultiDict[str, str] = dataclasses.field(default_factory=lambda: ImmutableMultiDict())
        body: dict[str, Any] = dataclasses.field(default_factory=lambda: {})
        headers: dict[str, str] = dataclasses.field(default_factory=lambda: {})
        cookies: dict[str, str] = dataclasses.field(default_factory=lambda: {})

        # user injected by protected decorator
        user: DefaultAuthProvider.User | None = None

    @dataclasses.dataclass
    class RouteResponse:
        status_code: int = 200
        body: dict | str = dataclasses.field(default_factory=lambda: {})
        headers: dict = dataclasses.field(default_factory=lambda: {})
        cookies: List[dict] = dataclasses.field(default_factory=lambda: [])
        content_type: str | None = None

    path: str
    name: str
    handler: Callable[[RouteRequest], RouteResponse | dict | str]
    method: str = "GET"
    public: bool = False
    content_type: str | None = None


class _HasConfig:
    config: AdminTableConfig

    def __init__(self, config: AdminTableConfig):
        self.config = config

    def get_resource(self, resource_name: str) -> "Resource":
        resource = next((resource for resource in self.config.resources or [] if resource.name == resource_name), None)
        if resource is None:
            raise ValueError(f"Resource '{resource_name}' not found")
        return resource

    @staticmethod
    def get_view_create(resource: "Resource") -> "CreateView":
        if (view := resource.views.create) is None:
            raise ValueError(f"Resource '{resource.name}' has no create view configured")
        return view

    @staticmethod
    def get_view_detail(resource: "Resource") -> "DetailView":
        if (view := resource.views.detail) is None:
            raise ValueError(f"Resource '{resource.name}' has no detail view configured")
        return view

    @staticmethod
    def get_view_list(resource: "Resource") -> "ListView":
        if (view := resource.views.list) is None:
            raise ValueError(f"Resource '{resource.name}' has no list view configured")
        return view


class AuthRouteMixin(_HasConfig):
    @staticmethod
    def protected(
        handler: Callable[["AdminTable", AdminTableRoute.RouteRequest], AdminTableRoute.RouteResponse],
    ) -> Callable[["AdminTable", AdminTableRoute.RouteRequest], AdminTableRoute.RouteResponse]:
        def wrapped(admin_table: "AdminTable", request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
            if not (authorization := request.headers.get("Authorization", request.headers.get("authorization"))):
                return AdminTableRoute.RouteResponse(
                    status_code=401,
                    body={"message": "Unauthorized"},
                    content_type="application/json",
                )

            token = authorization.removeprefix("Bearer ")
            if not (user := admin_table.config.auth_provider.validate_token(token)):
                return AdminTableRoute.RouteResponse(
                    status_code=401,
                    body={"message": "Unauthorized"},
                    content_type="application/json",
                )

            request.user = user

            result = handler(admin_table, request)
            return result

        return wrapped


class _Column:
    def __init__(self, *, ref: str, display: str, sortable: bool, description: str | None = None, **kwargs):
        self.ref = ref
        self.display = display
        self.sortable = sortable
        self.description = description

    def value(self, row):
        return row[self.ref]

    def head(self):
        return {"ref": self.ref, "display": self.display, "sortable": self.sortable, "description": self.description}


class _LinkDetailColumn(_Column):
    def __init__(self, resource, id_ref, **kwargs):
        super().__init__(**kwargs)
        self.resource = resource
        self.id_ref = id_ref

    def value(self, row):
        return {
            "type": "link",
            "kind": "detail",
            "resource": self.resource,
            "value": row[self.ref],
            "id": row[self.id_ref],
            "href": f"/resource/{quote(self.resource)}/detail/{row[self.id_ref]}",
        }


class _LinkTableColumn(_Column):
    def __init__(self, resource, filter_col, filter_op, filter_ref, **kwargs):
        super().__init__(**kwargs)
        self.resource = resource
        self.filter_col = filter_col
        self.filter_op = filter_op
        self.filter_ref = filter_ref

    def value(self, row):
        return {
            "type": "link",
            "kind": "table",
            "resource": self.resource,
            "value": row[self.ref],
            "filter": {"col": self.filter_col, "op": self.filter_op, "val": row[self.filter_ref]},
            "href": f"/resource/{quote(self.resource)}/list"
            f"?filter={self.filter_col};{self.filter_op};{row[self.filter_ref]}",
        }


class _ComputedColumn(_Column):
    def __init__(self, handler, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler

    def value(self, row):
        try:
            value = self.handler(row)
        except Exception as e:
            print(f"Failed computing {self}: {e}", file=sys.stderr)
            value = "# ERROR #"

        if isinstance(value, str):
            return value
        # TODO support for returning links to details and lists

        return str(value)


def field_resolver(fields):
    for field in fields:
        # pattern match on the field type
        match field:
            # field is string
            case ref if isinstance(ref, str):
                yield _Column(display=ref, ref=ref, sortable=True)
                # TODO check if ref is a valid column in the model
            case ref if isinstance(ref, InstrumentedAttribute):
                yield _Column(display=ref.key, ref=ref.key, sortable=True)
            case [display, ref] if isinstance(ref, str):
                # TODO check if ref is a valid column in the model
                yield _Column(ref=ref, display=display, sortable=True)
            case [display, ref] if isinstance(ref, InstrumentedAttribute):
                yield _Column(ref=ref.key, display=display, sortable=True)
            case [display, ref] if isinstance(ref, LinkDetail):
                yield _LinkDetailColumn(ref.resource, ref.id_ref, ref=ref.ref, display=display, sortable=True)
            case [display, ref] if isinstance(ref, LinkTable):
                yield (
                    _LinkTableColumn(
                        ref.resource,
                        ref.filter_col,
                        ref.filter_op,
                        ref.filter_ref,
                        ref=ref.ref,
                        display=display,
                        sortable=True,
                    )
                )
            case [display, handler] if callable(handler):
                yield _ComputedColumn(handler, display=display, sortable=False)

            # same cases, but now with description
            # I did not come up with a better way to do this unfortunately
            case [display, description, ref] if isinstance(ref, str):
                yield _Column(display=display, ref=ref, sortable=True, description=description)
            case [display, description, ref] if isinstance(ref, InstrumentedAttribute):
                yield _Column(display=display, ref=ref.key, sortable=True, description=description)
            case [display, description, ref] if isinstance(ref, LinkDetail):
                yield _LinkDetailColumn(
                    ref.resource, ref.id_ref, ref=ref.ref, display=display, sortable=True, description=description
                )
            case [display, description, ref] if isinstance(ref, LinkTable):
                yield (
                    _LinkTableColumn(
                        ref.resource,
                        ref.filter_col,
                        ref.filter_op,
                        ref.filter_ref,
                        ref=ref.ref,
                        display=display,
                        sortable=True,
                        description=description,
                    )
                )
            case [display, description, handler] if callable(handler):
                yield _ComputedColumn(ref, ref=None, display=display, sortable=False, description=description)

            case _:
                raise ValueError(f"Invalid field definition: {field}")


class ListViewMixin(AuthRouteMixin, _HasConfig):
    @AuthRouteMixin.protected
    def resource_list_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        view = self.get_view_list(resource)

        current_page = int(request.query_params.get("page", 1) or 1)
        current_per_page = int(request.query_params.get("per_page", 50) or 50)
        raw_filters: List[Any] = [x.split(";") for x in request.query_params.getlist("filter")]
        current_sort = (request.query_params.get("sort", df := f"{resource.id_col};desc") or df).split(";")

        # ##### GENERATE DATA USING RESOLVER
        title = view.title or resource.display or resource.name
        description = view.description() if callable(view.description) else view.description
        has_create = resource.views.create is not None

        # remap filters to the format expected by the resolver
        resolved_filters = resource.resolver.get_filter_options(resource)
        current_filters = [
            # apply filter processor if defined
            (view.filter_processor or (lambda f: f))(
                ResolverBase.AppliedFilter(ref=ref, op=op, val=val, display=resolved_filters[ref].display)
            )
            for ref, op, val in raw_filters
        ]

        header: List[_Column] = []
        if resource.views.detail is not None:
            header.append(
                _LinkDetailColumn(
                    resource=resource.name,
                    id_ref=resource.id_col,
                    ref=view.detail_value_ref or resource.id_col,
                    display="Detail",
                    sortable=True,
                )
            )
        header.extend(field_resolver(view.fields))

        data = resource.resolver.resolve_list(
            resource,
            current_page,
            current_per_page,
            current_filters,
            cast(Tuple[str, Literal["asc", "desc"]], current_sort),
        )

        # ##### PROCESS DATA INTO COLUMN FORMAT
        rows = [[h.value(row) for h in header] for row in data.list_data]

        # ##### RESPONSE GENERATION

        body = {
            "data": rows,
            "header": [h.head() for h in header],
            "meta": {
                "title": title,
                "description": description,
                "has_create": has_create,
            },
            "applied_filters": [
                {
                    "ref": f.ref,
                    "op": f.op,
                    "val": f.val,
                    "display": f.display,
                }
                for f in current_filters
            ],
            "available_filters": [
                {
                    "ref": rf.reference,
                    "display": rf.display,
                }
                for rf in resolved_filters.values()
            ],
            "pagination": {
                "page": data.pagination["page"],
                "per_page": data.pagination["per_page"],
                "total": data.pagination["total"],
            },
        }

        return AdminTableRoute.RouteResponse(
            body=body,
            content_type="application/json",
        )


class AdminTable(ListViewMixin, _HasConfig):
    def __init__(self, config: "AdminTableConfig"):
        super().__init__(config)

        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui/index.html"))
        assert os.path.isfile(p), f"folder with UI not found at {p}"

    @property
    def routes(self) -> List[AdminTableRoute]:
        # noinspection PyTypeChecker
        return [
            AdminTableRoute(
                path="/ping",
                method="POST",
                name="ping",
                handler=self.ping_handler,
            ),
            AdminTableRoute(
                path="/login",
                method="POST",
                name="login",
                handler=self.login_handler,
            ),
            AdminTableRoute(
                path="/user",
                method="GET",
                name="userinfo",
                handler=self.user_handler,
            ),
            AdminTableRoute(
                path="/navigation",
                method="GET",
                name="navigation",
                handler=self.navigation_handler,
            ),
            AdminTableRoute(
                path="/resource/{resource}/list",
                method="GET",
                name="resource_list",
                handler=self.resource_list_handler,
            ),
            AdminTableRoute(
                path="/resource/{resource}/create",
                method="GET",
                name="resource_create_get_schema",
                handler=self.resource_create_get_schema_handler,
            ),
            AdminTableRoute(
                path="/resource/{resource}/create",
                method="POST",
                name="resource_create",
                handler=self.resource_create_handler,
            ),
            AdminTableRoute(
                path="/resource/{resource}/detail/{detail_id}",
                method="GET",
                name="resource_detail",
                handler=self.resource_detail_handler,
            ),
            AdminTableRoute(
                path="/resource/{resource}/detail/{detail_id}/action/{action_ref}",
                method="POST",
                name="resource_detail",
                handler=self.resource_action_call_handler,
            ),
            AdminTableRoute(
                path="/page/{page_name}/view",
                method="GET",
                name="page_view",
                handler=self.page_view_handler,
            ),
            AdminTableRoute(
                path="/dashboard",
                method="GET",
                name="get_dashboard",
                handler=self.dashboard_handler,
            ),
            AdminTableRoute(path="/{path:path}", method="GET", name="catch_all", handler=self.default_handler),
        ]

    @AuthRouteMixin.protected
    def user_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        return AdminTableRoute.RouteResponse(
            body={"user": dataclasses.asdict(request.user) if request.user else None},
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def ping_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        return AdminTableRoute.RouteResponse(
            body={"message": "pong", "user": dataclasses.asdict(request.user) if request.user else None},
            content_type="application/json",
        )

    def login_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        assert self.config.auth_provider is not None, "No auth provider configured"
        try:
            user = self.config.auth_provider.authenticate(request.body.get("username"), request.body.get("password"))
        except Exception as e:
            return AdminTableRoute.RouteResponse(
                status_code=500,
                body={"message": f"Internal server error: {e}"},
                content_type="application/json",
            )
        if isinstance(user, self.config.auth_provider.User):
            token = self.config.auth_provider.generate_token(user)
            return AdminTableRoute.RouteResponse(
                body={"message": "login successful", "token": token},
                content_type="application/json",
            )
        return AdminTableRoute.RouteResponse(
            status_code=401,
            body={"message": "login failed"},
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def navigation_handler(self, r: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        href_base = f"{r.url.scheme}://{r.url.host}:{r.url.port}{r.url.path.removesuffix('/navigation')}"

        # TODO allow for custom drawer ordering
        drawers = []
        for res in self.config.resources + self.config.pages:
            drawers.append(res.navigation) if res.navigation not in drawers else None

        return AdminTableRoute.RouteResponse(
            body={
                "name": self.config.name,
                "links": [
                    {
                        "name": drawer,
                        "children": [
                            {
                                "name": resource.name,
                                "display": resource.display or resource.name,
                                "href": {"list": f"{href_base}/resource/{quote(resource.name)}/list"},
                                "type": "resource",
                            }
                            for resource in self.config.resources
                            if resource.navigation == drawer
                        ]
                        + [
                            {
                                "name": page.name,
                                "display": page.display or page.name,
                                "href": {"view": f"{href_base}/page/{quote(page.name)}/view"},
                                "type": "page",
                            }
                            for page in self.config.pages
                            if page.navigation == drawer
                        ],
                    }
                    for drawer in drawers
                ],
            },
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def page_view_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        page_name = unquote(request.path_params["page_name"])
        for page in self.config.pages:
            if page.name == page_name:
                return AdminTableRoute.RouteResponse(
                    body={
                        "display": page.display,
                        "name": page.name,
                        "content": page.content(request) if callable(page.content) else page.content,
                        "type": page.type,
                    },
                    content_type="application/json",
                )
        return AdminTableRoute.RouteResponse(
            status_code=404,
            body={"message": f"Page {page_name} not found"},
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def resource_create_get_schema_handler(
        self, request: AdminTableRoute.RouteRequest
    ) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        view = self.get_view_create(resource)

        return AdminTableRoute.RouteResponse(
            body={
                "schema": view.schema.model_json_schema(),
            },
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def resource_create_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        view = self.get_view_create(resource)

        try:
            data = view.schema(**request.body)
            callback_ret = view.callback(data)
        except Exception as e:
            return AdminTableRoute.RouteResponse(
                status_code=200,
                body={"message": f"Invalid data: {e}", "failed": True},
                content_type="application/json",
            )

        if hasattr(callback_ret, resource.id_col):
            return AdminTableRoute.RouteResponse(
                body={
                    "message": "Resource created",
                    "redirect": {
                        "type": "detail",
                        "resource": resource.name,
                        "id": getattr(callback_ret, resource.id_col),
                    },
                },
                content_type="application/json",
            )

        # TODO handle user-defined redirect

        return AdminTableRoute.RouteResponse(
            body={
                "message": str(callback_ret or "Resource created"),
            },
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def resource_detail_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        detail = self.get_view_detail(resource)

        entry = resource.resolver.resolve_detail(resource, request.path_params["detail_id"])

        fields = [(field.head(), field.value(entry)) for field in field_resolver(detail.fields)]

        title_template = string.Template(detail.title or resource.display or resource.name)
        title = title_template.safe_substitute(entry)

        def get_param(attr: str, param: Parameter) -> dict[str, Any]:
            type_map = {int: "int", str: "str", Parameter.empty: "str", bool: "bool"}
            description = next(
                (
                    y
                    for y in (getattr(x, "documentation", None) for x in getattr(param.annotation, "__metadata__", []))
                    if y
                ),
                None,
            )
            value_type = getattr(param.annotation, "__origin__", param.annotation)
            assert value_type in type_map, f"Unsupported type: {value_type}"

            return {
                "attr": attr,
                "title": attr.replace("_", " ").title(),
                "type": type_map[value_type],
                "required": param.default == Parameter.empty,
                "description": description,
            }

        actions = []
        for action in detail.actions:
            actions.append(
                {
                    "title": action.__name__.replace("_", " ").title(),
                    "ref": action.__name__,
                    "description": action.__doc__ or "",
                    "parameters": [
                        get_param(attr, param)
                        for attr, param in signature(action).parameters.items()
                        if attr != "self"
                        and getattr(param.annotation, "__origin__", param.annotation)
                        in [int, str, bool, Parameter.empty]
                    ],
                }
            )

        tables = []
        for table in detail.tables:
            tables.append(
                {
                    "title": table.title,
                    "description": table.description,
                    "resource": table.resource,
                    "filter": {
                        "col": table.filter_col,
                        "op": table.filter_op,
                        "val": entry[table.filter_ref],
                    },
                }
            )

        return AdminTableRoute.RouteResponse(
            body={
                "title": title,
                "fields": fields,
                "actions": actions,
                "tables": tables,
            },
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def resource_action_call_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        detail = self.get_view_detail(resource)

        action = next((a for a in detail.actions if a.__name__ == request.path_params["action_ref"]), None)
        if not action:
            return AdminTableRoute.RouteResponse(
                status_code=200,
                body={"message": f"Invalid action ref: {request.path_params["action_ref"]}", "failed": True},
                content_type="application/json",
            )
        entry = resource.resolver.resolve_detail(resource, request.path_params["detail_id"])

        # TODO build params
        raw_params = request.body["params"]
        params = {**raw_params}

        try:
            ret = action(entry, **params)
        except Exception as e:
            logging.exception(f"Failed calling action: {e}")
            return AdminTableRoute.RouteResponse(
                status_code=200,
                body={"message": f"Failed calling action: {e}", "failed": True},
                content_type="application/json",
            )

        return AdminTableRoute.RouteResponse(
            body={"message": str(ret) or "Action call success"},
            content_type="application/json",
        )

    @AuthRouteMixin.protected
    def dashboard_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        if not request.user:
            return AdminTableRoute.RouteResponse(
                status_code=401,
                body={"message": "Unauthorized"},
                content_type="application/json",
            )
        try:
            content = self.config.dashboard(request.user)
            return AdminTableRoute.RouteResponse(
                body={"content": content},
                content_type="application/json",
            )
        except Exception as e:
            return AdminTableRoute.RouteResponse(
                status_code=500,
                body={"message": f"Internal server error: {e}"},
                content_type="application/json",
            )

    def default_handler(self, request: AdminTableRoute.RouteRequest, fallback=True) -> AdminTableRoute.RouteResponse:
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui/", request.path_params["path"] or "index.html"))
        try:
            with open(p) as f:
                data = f.read()
                print("data", data[:100])
                return AdminTableRoute.RouteResponse(
                    status_code=200,
                    body=data,
                    content_type={"html": "text/html", "js": "text/javascript", "css": "text/css"}.get(
                        p.split(".")[-1], "text/plain"
                    ),
                )
        except FileNotFoundError:
            if fallback:
                return self.default_handler(
                    AdminTableRoute.RouteRequest(url=request.url, path_params={"path": ""}), fallback=False
                )
            return AdminTableRoute.RouteResponse(
                status_code=404,
                body="Not Found",
            )
