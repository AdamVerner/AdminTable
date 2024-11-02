import asyncio
import dataclasses
import datetime
import logging
import os.path
import string
import sys
from collections.abc import Awaitable, Callable
from inspect import Parameter, signature
from typing import Any, Literal, Protocol, TypedDict, cast
from urllib.parse import quote, unquote

from sqlalchemy.orm import InstrumentedAttribute
from starlette.datastructures import ImmutableMultiDict

from .config import (
    AdminTableConfig,
    CreateView,
    DefaultAuthProvider,
    DetailView,
    GetGraphCallback,
    GraphData,
    InputForm,
    LinkDetail,
    LinkTable,
    ListView,
    LiveValue,
    Page,
    RedirectCustomPage,
    RedirectDetail,
    RedirectList,
    RefreshView,
    Resource,
)
from .modules.bases import ResolverBase


@dataclasses.dataclass
class URL:
    scheme: str | None
    host: str | None
    port: int | None
    path: str | None
    query: str | None


class _WebsocketClose(Protocol):
    def __call__(self, code: int = 1000, reason: str | None = None) -> Awaitable[None]: ...


@dataclasses.dataclass
class AdminTableWebsocket:
    """
    Specification of websocket "endpoint"
    """

    @dataclasses.dataclass
    class Websocket:
        url: URL
        path_params: dict[str, str]
        query_params: ImmutableMultiDict[str, str]
        headers: dict[str, str]
        cookies: dict[str, str]

        accept: Callable[[], Awaitable[None]]
        receive_json: Callable[[], Awaitable[dict[str, str]]]
        send_json: Callable[[dict[str, str]], Awaitable[None]]
        close: _WebsocketClose

    path: str
    name: str

    accept: Callable[["AdminTableWebsocket.Websocket"], Awaitable[None]]
    handle: Callable[["AdminTableWebsocket.Websocket"], Awaitable[None]]
    disconnected: Callable[["AdminTableWebsocket.Websocket"], Awaitable[None]]
    onerror: Callable[["AdminTableWebsocket.Websocket", Exception], Awaitable[None]] | None = None
    finish: Callable[["AdminTableWebsocket.Websocket"], Awaitable[None]] | None = None


@dataclasses.dataclass
class AdminTableRoute:
    @dataclasses.dataclass
    class RouteRequest:
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
        cookies: list[dict] = dataclasses.field(default_factory=lambda: [])
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
            raise ValueError(f"Resource not found: {resource}")
        return resource

    @staticmethod
    def get_view_create(resource: "Resource") -> "CreateView":
        if (view := resource.views.create) is None:
            raise ValueError(f"Create view for Resource not found: {resource}")
        return view

    @staticmethod
    def get_view_detail(resource: "Resource") -> "DetailView":
        if (view := resource.views.detail) is None:
            raise ValueError(f"Detail for Resource not found: {resource}")
        return view

    @staticmethod
    def get_view_list(resource: "Resource") -> "ListView":
        if (view := resource.views.list) is None:
            raise ValueError(f"List for Resource not found: {resource}")
        return view

    def get_input_form(self, location_name: str) -> "InputForm":
        input_form = next((form for form in self.config.input_forms if form.location == location_name), None)
        if input_form is None:
            raise ValueError(f"Input Form not found: {location_name}")
        return input_form

    def get_page(self, page_name: str) -> "Page":
        unquoted = unquote(page_name)

        page = next((p for p in self.config.pages if p.name == unquoted), None)
        if page is None:
            raise ValueError("Page not found, invalid page name")
        return page


class AuthRouteMixin(_HasConfig):
    @staticmethod
    def user_from_header(
        admin_table: "AdminTable", headers: dict[str, str]
    ) -> AdminTableRoute.RouteResponse | DefaultAuthProvider.User:
        # check if bearer is passed in websocket protocol
        if bearer := headers.get("sec-websocket-protocol", headers.get("Sec-WebSocket-Protocol")):
            authorization = bytes.fromhex(bearer.removeprefix("bearer")).decode("utf-8")
        else:
            authorization = headers.get("Authorization", headers.get("authorization") or "")

        if not authorization:
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

        return user

    @staticmethod
    def check_request(
        admin_table: "AdminTable", request: AdminTableRoute.RouteRequest
    ) -> AdminTableRoute.RouteResponse | None:
        r = AuthRouteMixin.user_from_header(admin_table, request.headers)
        if isinstance(r, AdminTableRoute.RouteResponse):
            return r
        request.user = r
        return None

    @staticmethod
    def protected(
        handler: Callable[["AdminTable", AdminTableRoute.RouteRequest], AdminTableRoute.RouteResponse],
    ) -> Callable[["AdminTable", AdminTableRoute.RouteRequest], AdminTableRoute.RouteResponse]:
        def wrapped(admin_table: "AdminTable", request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
            if (response := AuthRouteMixin.check_request(admin_table, request)) is not None:
                return response

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

    def head(self, current_sort: tuple[str, Literal["asc", "desc"]] | None = None):
        sort = None
        if current_sort:
            sort = current_sort[1] if current_sort[0] == self.ref else None
        return {
            "ref": self.ref,
            "display": self.display,
            "sortable": self.sortable,
            "sort": sort,
            "description": self.description,
        }


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


class _LiveValueColumn(_Column):
    def __init__(self, initial_value_ref: str | None, topic_ref: str, history: bool, **kwargs):
        self.initial_value_ref = initial_value_ref
        self.topic_ref = topic_ref
        self.history = history
        super().__init__(**kwargs)

    def value(self, row):
        return {
            "type": "live",
            "initial": row[self.initial_value_ref] if self.initial_value_ref else None,
            "topic": row[self.topic_ref],
            "history": self.history,
        }


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
            case [display, handler] if callable(handler):
                yield _ComputedColumn(handler, ref=None, display=display, sortable=False)
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
            case [display, ref] if isinstance(ref, LiveValue):
                yield _LiveValueColumn(
                    ref.initial_ref, ref.ref, ref.history, ref=ref.initial_ref, display=display, sortable=True
                )

            # same cases, but now with description
            # I did not come up with a better way to do this unfortunately
            case [display, description, ref] if isinstance(ref, str):
                yield _Column(display=display, ref=ref, sortable=True, description=description)
            case [display, description, ref] if isinstance(ref, InstrumentedAttribute):
                yield _Column(display=display, ref=ref.key, sortable=True, description=description)
            case [display, description, handler] if callable(handler):
                yield _ComputedColumn(ref, ref=None, display=display, sortable=False, description=description)
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
            case [display, description, ref] if isinstance(ref, LiveValue):
                yield _LiveValueColumn(
                    ref.initial_ref,
                    ref.ref,
                    ref.history,
                    ref=ref.initial_ref,
                    display=display,
                    sortable=False,
                    description=description,
                )

            case _:
                raise ValueError(f"Invalid field definition: {field}")


class ListViewMixin(AuthRouteMixin, _HasConfig):
    @AuthRouteMixin.protected
    def resource_list_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        view = self.get_view_list(resource)

        current_page = int(request.query_params.get("page", 1) or 1)
        current_per_page = int(request.query_params.get("per_page", 50) or 50)
        raw_filters: list[Any] = [x.split(";") for x in request.query_params.getlist("filter")]
        default_sort = f"{view.default_sort[0] or resource.id_col};{view.default_sort[1]}"
        current_sort = cast(
            tuple[str, Literal["asc", "desc"]],
            (request.query_params.get("sort", default_sort) or default_sort).split(";"),
        )

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

        header: list[_Column] = []
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
            current_filters + (view.hidden_filters or []),
            current_sort,
        )

        # ##### PROCESS DATA INTO COLUMN FORMAT
        rows = [[h.value(row) for h in header] for row in data.list_data]

        # ##### RESPONSE GENERATION

        body = {
            "data": rows,
            "header": [h.head(current_sort) for h in header],
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
    class LiveDataTopic(TypedDict):
        task: asyncio.Task
        clients: list["AdminTableWebsocket.Websocket"]

    _subscriber_info: dict[str, LiveDataTopic]

    def __init__(self, config: "AdminTableConfig"):
        super().__init__(config)

        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui/index.html"))
        assert os.path.isfile(p), f"folder with UI not found at {p}"

        self._subscriber_info: dict[str, AdminTable.LiveDataTopic] = {}

    @property
    def routes(self) -> list[AdminTableRoute]:
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
                path="/resource/{resource}/detail/{detail_id}/graph/{graph_ref}",
                method="GET",
                name="resource_graph",
                handler=self.resource_graph_handler,
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
            AdminTableRoute(
                path="/input_form/{location}",
                method="GET",
                name="get_input_form",
                handler=self.get_input_form_handler,
            ),
            AdminTableRoute(
                path="/input_form/{location}",
                method="POST",
                name="submit_input_form",
                handler=self.submit_input_form_handler,
            ),
            AdminTableRoute(path="/{path:path}", method="GET", name="catch_all", handler=self.default_handler),
        ]

    async def live_data_websocket_accept(self, ws: AdminTableWebsocket.Websocket):
        r = AdminTable.user_from_header(self, ws.headers)
        if isinstance(r, AdminTableRoute.RouteResponse):
            if isinstance(r.body, str):
                await ws.close(401, r.body)
            else:
                await ws.close(401, r.body.get("message", "Unauthorized"))

            raise Exception("Unauthorized")

        # TODO check if user can access topic
        print("accepting connection on: ", ws.url.path, "form: ", r)
        await ws.accept()

    async def live_data_topic_task(self, topic: str):
        """
        live data manager task. For new subscribed topic, spins up "live data" task
        and broadcasts data to all clients.
        """

        info = self._subscriber_info.get(topic, None)
        assert info is not None, f"topic {topic} not in subscriber info"
        assert self.config.live_data_manager is not None, "No live data manager configured"

        try:
            async with self.config.live_data_manager(topic) as topic_iterable:
                # if there are no clients, stop producing data
                while info["clients"]:
                    data = await anext(topic_iterable)

                    clients = list(info["clients"])
                    excs = await asyncio.gather(
                        *(c.send_json({"value": data.value}) for c in clients), return_exceptions=True
                    )
                    for client, exc in zip(clients, excs):
                        if exc and client in info["clients"]:
                            info["clients"].remove(client)

                await topic_iterable.aclose()
        finally:
            self._subscriber_info.pop(topic, None)
            await asyncio.gather(*(c.close() for c in info["clients"]), return_exceptions=True)

    async def live_data_websocket_handler(self, ws: AdminTableWebsocket.Websocket) -> None:
        topic = ws.query_params["topic"]

        # if this is the first topic subscriber, create the topic production task
        if topic not in self._subscriber_info:
            task = asyncio.create_task(self.live_data_topic_task(topic))
            self._subscriber_info[topic] = {
                "task": task,
                "clients": [ws],
            }
        else:
            self._subscriber_info[topic]["clients"].append(ws)

        # loop forever, until client disconnects (raises ConnectionClosed)
        while True:
            msg = await ws.receive_json()
            print(f'received message "{msg}" on ws: {ws.url.path}. There should be no messages here', file=sys.stderr)

    async def live_data_websocket_disconnect(self, ws: AdminTableWebsocket.Websocket):
        topic = ws.query_params["topic"]
        if tpc := self._subscriber_info.get(topic):
            tpc["clients"].remove(ws) if ws in tpc["clients"] else None

    @property
    def websockets(self) -> list[AdminTableWebsocket]:
        return [
            AdminTableWebsocket(
                path="/ws/live_data",
                name="websocket",
                accept=self.live_data_websocket_accept,
                handle=self.live_data_websocket_handler,
                disconnected=self.live_data_websocket_disconnect,
            )
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
        href_base = f"{r.url.scheme}://{r.url.host}:{r.url.port}{(r.url.path or '').removesuffix('/navigation')}"

        # TODO allow for custom drawer ordering
        drawers = []
        for res in self.config.resources + self.config.pages:
            drawers.append(res.navigation) if res.navigation not in drawers else None

        return AdminTableRoute.RouteResponse(
            body={
                "name": self.config.name,
                "icon_src": self.config.icon_src,
                "version": self.config.version,
                "navigation": [
                    {
                        "name": drawer,
                        "icon": self.config.navigation_icons.get(drawer or "", "x") or "x",
                        "links": [
                            {
                                "name": resource.name,
                                "display": resource.display or resource.name,
                                "href": {"list": f"{href_base}/resource/{quote(resource.name)}/list"},
                                "type": "resource",
                            }
                            for resource in self.config.resources
                            if resource.navigation == drawer and not resource.hidden
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

    def page_view_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        page = self.get_page(request.path_params["page_name"])

        # check request authentication for non-public forms
        if not page.public and (response := AuthRouteMixin.check_request(self, request)) is not None:
            return response

        return AdminTableRoute.RouteResponse(
            body={
                "display": page.display,
                "name": page.name,
                "content": page.content(request) if callable(page.content) else page.content,
                "type": page.type,
            },
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

        return self.process_handler_return(callback_ret, current_resource=resource)

    @AuthRouteMixin.protected
    def resource_detail_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        detail = self.get_view_detail(resource)

        entry = resource.resolver.resolve_detail(resource, request.path_params["detail_id"])

        if entry is None:
            return AdminTableRoute.RouteResponse(
                status_code=404,
                body={"message": f"Resource not found: {request.path_params['detail_id']}"},
                content_type="application/json",
            )

        fields = [(field.head(None), field.value(entry)) for field in field_resolver(detail.fields)]

        title_template = string.Template(detail.title or resource.display or resource.name)
        title = title_template.safe_substitute(entry)

        description = detail.description(entry) if callable(detail.description) else detail.description

        def get_param(attr: str, param: Parameter) -> dict[str, Any]:
            type_map = {int: "int", str: "str", Parameter.empty: "str", bool: "bool"}
            desc = next(
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
                "description": desc,
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

        graphs = []
        for graph in detail.graphs:
            ref = graph.__name__
            display = graph.__name__.replace("_", " ").title()
            graphs.append(
                {
                    "title": display,
                    "description": graph.__doc__ or "",
                    "reference": ref,
                }
            )

        return AdminTableRoute.RouteResponse(
            body={
                "title": title,
                "description": description,
                "fields": fields,
                "actions": actions,
                "tables": tables,
                "graphs": graphs,
            },
            content_type="application/json",
        )

    def resource_graph_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        resource = self.get_resource(request.path_params["resource"])
        detail = self.get_view_detail(resource)
        data_function: GetGraphCallback | None = next(
            (g for g in detail.graphs if g.__name__ == request.path_params["graph_ref"]), None
        )

        if data_function is None:
            return AdminTableRoute.RouteResponse(
                status_code=404,
                body={"message": f"Graph {request.path_params['graph_ref']} not found"},
                content_type="application/json",
            )
        entry = resource.resolver.resolve_detail(resource, request.path_params["detail_id"])

        if entry is None:
            return AdminTableRoute.RouteResponse(
                status_code=404,
                body={"message": f"Resource not found: {request.path_params['detail_id']}"},
                content_type="application/json",
            )

        if (range_type := request.query_params.get("range_type", "date")) == "date":
            q_range_from = request.query_params.get("range_from", None)
            q_range_to = request.query_params.get("range_to", None)

            range_from = datetime.datetime.fromisoformat(q_range_from) if q_range_from else None
            range_to = datetime.datetime.fromisoformat(q_range_to) if q_range_to else None
        elif range_type is not None:
            return AdminTableRoute.RouteResponse(
                status_code=400,
                body={"message": f"Invalid range type: {range_type}"},
                content_type="application/json",
            )
        else:
            range_from = range_to = None

        try:
            graph_data: GraphData = data_function(entry, range_from=range_from, range_to=range_to)
        except Exception as e:
            logging.exception("Failed getting graph data")
            return AdminTableRoute.RouteResponse(
                status_code=500,
                body={"message": f"Internal server error: {e}"},
                content_type="application/json",
            )

        return AdminTableRoute.RouteResponse(
            body=graph_data.to_dict(),
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
        if entry is None:
            return AdminTableRoute.RouteResponse(
                status_code=404,
                body={"message": f"Resource not found: {request.path_params['detail_id']}"},
                content_type="application/json",
            )

        # TODO build params
        raw_params = request.body["params"]
        params = {**raw_params}

        try:
            ret = action(entry, **params)
            return self.process_handler_return(ret)
        except Exception as e:
            logging.exception(f"Failed calling action: {e}")
            return AdminTableRoute.RouteResponse(
                status_code=200,
                body={"message": f"Failed calling action: {e}", "failed": True},
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

    def get_input_form_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        form = self.get_input_form(request.path_params["location"])

        # check request authentication for non-public forms
        if not form.public and (response := AuthRouteMixin.check_request(self, request)) is not None:
            return response

        description = form.description() if callable(form.description) else form.description

        return AdminTableRoute.RouteResponse(
            status_code=200,
            body={
                "title": form.title,
                "public": form.public,
                "description": description,
                "schema": form.schema.model_json_schema(),
            },
            content_type="application/json",
        )

    def submit_input_form_handler(self, request: AdminTableRoute.RouteRequest) -> AdminTableRoute.RouteResponse:
        form = self.get_input_form(request.path_params["location"])

        # check request authentication for non-public forms
        if not form.public and (response := AuthRouteMixin.check_request(self, request)) is not None:
            return response

        try:
            data = form.schema(**request.body)
            callback_ret = form.callback(data)
            return self.process_handler_return(callback_ret)
        except Exception as e:
            return AdminTableRoute.RouteResponse(
                status_code=500,
                body={"message": f"error: {e}"},
                content_type="application/json",
            )

    def default_handler(self, request: AdminTableRoute.RouteRequest, fallback=True) -> AdminTableRoute.RouteResponse:
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui/", request.path_params["path"] or "index.html"))
        try:
            with open(p) as f:
                data = f.read()
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

    def process_handler_return(
        self, callback_ret: Any, current_resource: Resource | None = None
    ) -> AdminTableRoute.RouteResponse:
        if isinstance(callback_ret, RefreshView):
            return AdminTableRoute.RouteResponse(
                body={"message": callback_ret.message or "Success", "refresh": True},
                content_type="application/json",
            )

        if isinstance(callback_ret, RedirectDetail):
            return AdminTableRoute.RouteResponse(
                body={
                    "message": callback_ret.message or "Success",
                    "redirect": {
                        "type": "detail",
                        "resource": callback_ret.resource,
                        "id": callback_ret.id,
                    },
                },
                content_type="application/json",
            )

        if isinstance(callback_ret, RedirectList):
            return AdminTableRoute.RouteResponse(
                body={
                    "message": callback_ret.message or "Success",
                    "redirect": {
                        "type": "list",
                        "resource": callback_ret.resource,
                        "filters": [
                            {
                                "ref": f.ref,
                                "op": f.op,
                                "val": f.val,
                                "display": f.display,
                            }
                            for f in callback_ret.filters
                        ],
                    },
                },
                content_type="application/json",
            )

        if isinstance(callback_ret, RedirectCustomPage):
            return AdminTableRoute.RouteResponse(
                body={
                    "message": callback_ret.message or "Success",
                    "redirect": {
                        "type": "page",
                        "page": callback_ret.page_name,
                    },
                },
                content_type="application/json",
            )

        if isinstance(callback_ret, str):
            return AdminTableRoute.RouteResponse(
                body={"message": callback_ret},
                content_type="application/json",
            )

        if current_resource:
            if isinstance(callback_ret, dict) and "id" in callback_ret and current_resource:
                return self.process_handler_return(
                    RedirectDetail(resource=current_resource.name, id=callback_ret["id"])
                )
            if hasattr(callback_ret, "id") and current_resource:
                return self.process_handler_return(RedirectDetail(resource=current_resource.name, id=callback_ret.id))

        if callback_ret is None:
            return AdminTableRoute.RouteResponse(
                body={"message": "Success"},
                content_type="application/json",
            )
        raise TypeError(f"Invalid handler response type: {type(callback_ret)}")
