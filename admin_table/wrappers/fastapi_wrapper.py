import sys
import traceback
from collections.abc import Awaitable
from datetime import datetime
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..application import URL, AdminTableRoute, AdminTableWebsocket
from ._base import BaseWrapper

custom_encoder = {
    datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"),
}


class FastAPIWrapper(BaseWrapper):
    fa: FastAPI

    def __init__(self, *args, **kwargs):
        self.fa = FastAPI()
        super().__init__(*args, **kwargs)

        self.register_all()

    def register_route_callback(self, route: AdminTableRoute) -> None:
        async def callback(request: Request, payload: Any = Body(None)) -> Any:
            # create payload for route handler
            handler_request = AdminTableRoute.RouteRequest(
                url=URL(
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
            try:
                response = await route.handler(handler_request)
            except Exception:
                traceback.print_exc(5, sys.stderr)
                raise

            # process handler response
            if isinstance(response, str):
                return Response(content=response, media_type=route.content_type)
            if isinstance(response, dict):
                return JSONResponse(content=jsonable_encoder(response, custom_encoder=custom_encoder))
            if isinstance(response, AdminTableRoute.RouteResponse):
                content_type = response.headers.get("content-type", None) or response.content_type or route.content_type
                handler_response: JSONResponse | Response
                if content_type == "application/json":
                    handler_response = JSONResponse(
                        content=jsonable_encoder(response.body, custom_encoder=custom_encoder),
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

    def register_websocket_callback(self, websocket: AdminTableWebsocket) -> None:
        async def handler(ws: WebSocket) -> None:
            ws_wrap = AdminTableWebsocket.Websocket(
                url=URL(
                    scheme=ws.url.scheme,
                    host=ws.url.hostname,
                    port=ws.url.port,
                    path=ws.url.path,
                    query=ws.url.query,
                ),
                path_params=ws.path_params,
                query_params=ws.query_params,
                headers={k: v for k, v in ws.headers.items()},
                cookies=ws.cookies,
                accept=ws.accept,
                receive_json=ws.receive_json,
                send_json=ws.send_json,
                close=ws.close,
            )

            try:
                await websocket.accept(ws_wrap)
                await websocket.handle(ws_wrap)
            except WebSocketDisconnect:
                await websocket.disconnected(ws_wrap)
            except Exception as e:
                if websocket.onerror:
                    await websocket.onerror(ws_wrap, e)
                raise
            finally:
                if websocket.finish:
                    await websocket.finish(ws_wrap)

        self.fa.add_websocket_route(websocket.path, handler, websocket.name)

    def register_all(self):
        # if self.admin_table.auth_provider:
        #    self.fa.dependencies.append(self.auth_dependency)

        for route in self.admin_table.routes:
            self.register_route_callback(route)

        for websocket in self.admin_table.websockets:
            self.register_websocket_callback(websocket)

    def __call__(self, scope: Scope, receive: Receive, send: Send) -> Awaitable[None]:
        return self.fa(scope, receive, send)
