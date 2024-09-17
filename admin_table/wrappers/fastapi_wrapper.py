from typing import Any, Awaitable

from fastapi import Body, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from starlette.types import Receive, Scope, Send

from ..application import AdminTableRoute
from ._base import BaseWrapper


class FastAPIWrapper(BaseWrapper):
    fa: FastAPI

    def __init__(self, *args, **kwargs):
        self.fa = FastAPI()
        super().__init__(*args, **kwargs)

        self.register_routes()

    def register_route_callback(self, route: AdminTableRoute) -> None:
        async def callback(request: Request, payload: Any = Body(None)) -> Any:
            # create payload for route handler
            handler_request = AdminTableRoute.RouteRequest(
                url=AdminTableRoute.RouteRequest.URL(
                    scheme=request.url.scheme,
                    host=request.url.hostname,
                    port=request.url.port,
                    path=request.url.path,
                    query=request.url.query,
                ),
                path_params=request.path_params,
                query_params=request.query_params,
                body=payload,
                headers={k: v for k, v in request.headers.items()},
                cookies=request.cookies,
            )

            # call the route handler
            response = route.handler(handler_request)

            # process handler response
            if isinstance(response, str):
                return Response(content=response, media_type=route.content_type)
            if isinstance(response, dict):
                return JSONResponse(content=jsonable_encoder(response))
            if isinstance(response, AdminTableRoute.RouteResponse):
                content_type = response.headers.get("content-type", None) or response.content_type or route.content_type
                handler_response: JSONResponse | Response
                if content_type == "application/json":
                    handler_response = JSONResponse(
                        content=jsonable_encoder(response.body),
                        headers=response.headers,
                        status_code=response.status_code,
                    )
                else:
                    handler_response = Response(
                        content=response.body,
                        headers=response.headers,
                        status_code=response.status_code,
                        media_type=content_type,
                    )
                for cookie in response.cookies:
                    handler_response.set_cookie(**cookie)
                return handler_response
            raise TypeError(f"Invalid response type: {type(response)}")

        self.fa.add_api_route(route.path, callback, methods=[route.method], name=route.name)

    def register_routes(self):
        # if self.admin_table.auth_provider:
        #    self.fa.dependencies.append(self.auth_dependency)

        for route in self.admin_table.routes:
            self.register_route_callback(route)

    def __call__(self, scope: Scope, receive: Receive, send: Send) -> Awaitable[None]:
        return self.fa(scope, receive, send)
