import asyncio
import base64
import json
import os.path
import random
from collections.abc import AsyncIterable
from datetime import datetime, timedelta
from random import randrange
from typing import Annotated, Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field, create_model
from sqlalchemy import func, literal
from sqlalchemy.orm import Query, make_transient, make_transient_to_detached
from starlette import status
from starlette.responses import RedirectResponse
from typing_extensions import Doc

from admin_table import AdminTable, AdminTableConfig, Resource, ResourceViews
from admin_table.config import (
    CreateView,
    DetailView,
    InputForm,
    LineGraphData,
    LinkDetail,
    LinkTable,
    ListView,
    LiveDataManagerBase,
    LiveValue,
    Page,
    RedirectList,
    RefreshView,
    SubTable,
)
from admin_table.modules import SQLAlchemyResolver
from admin_table.modules.bases import ResolverBase
from admin_table.wrappers import FastAPIWrapper

from .base import Base, SessionLocal, engine
from .models import Item, User


def custom_user_action(
    user: User, string_param: Annotated[str, Doc("first param of the method")], int_param: int, bool_param: bool
) -> str:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    return f"performed action on {user} with params: {string_param}, {int_param}, {bool_param}"


async def another_action(user: User, bool_param: bool) -> RedirectList:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    with SessionLocal() as ss:
        ss.add(user)
        return RedirectList(
            resource="Items", filters=[SQLAlchemyResolver.AppliedFilter("id", "eq", str(user.items[-1].id))]
        )


def hello(user: User, b1: bool, b2: bool, string1: str, string2: str, string3: str) -> str:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    raise Exception("World")


def create_item(user: User, title: str, description: str, public: bool = False) -> RefreshView:
    """
    Creates new item
    """
    with SessionLocal() as ss:
        item = Item(title=title, description=description, public=public, owner_id=user.id)
        ss.add(item)
        ss.commit()
        return RefreshView(message=f"Created item {item}")


async def random_graph_data(
    user: User, range_from: datetime | None = None, range_to: datetime | None = None
) -> LineGraphData:
    range_from = range_from or (datetime.now() - timedelta(days=10))
    range_to = range_to or datetime.now()
    range_to, range_from = sorted([range_to, range_from], reverse=True)
    days = (range_to - range_from).days

    return LineGraphData(
        data=[
            {
                "date": range_from + timedelta(days=x),
                "Blue param": 150 - x * 10,
                "Red something": 50 + x * 2 + random.randint(-10, 15) * 10,
            }
            for x in range(days)
        ],
        dataKey="date",
        series=[
            {"name": "Blue param", "color": "indigo.6"},
            {"name": "Red something", "color": "red.6"},
        ],
    )


def generate_item_list_description() -> str:
    return (
        '## Some really cool graph\n'
        "```chart\n"
        f"{json.dumps(LineGraphData(
        data=[
            {
                "date": (datetime.now() + timedelta(days=x)).isoformat(),
                "Blue param": 150 - x * 10,
                "Red something": 50 + x * 2 + random.randint(-10, 15) * 10,
            }
            for x in range(100)
        ],
        dataKey="date",
        series=[
            {"name": "Blue param", "color": "indigo.6"},
            {"name": "Red something", "color": "red.6"},
        ],
    ).to_dict())}\n"
        "```\n"
    )


class LiveDataProducer(LiveDataManagerBase):
    def __init__(self, topic: str):
        super().__init__(topic)

    async def __aenter__(self) -> AsyncIterable[LiveDataManagerBase.DataEvent]:
        self.producer = self.produce()
        return self.producer

    async def __aexit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: Any) -> bool | None:
        await self.producer.aclose()
        return None

    async def produce(self):
        while True:
            await asyncio.sleep(1)
            yield self.DataEvent(value=str(randrange(100)))


async def create_user_function(model: Any) -> Any:
    with SessionLocal(expire_on_commit=False) as s:
        user = User(email=model.email)
        s.add(user)
        s.commit()

    make_transient(user)
    make_transient_to_detached(user)
    return user


icon_data = open(os.path.join(os.path.dirname(__file__), "icon.png"), "rb").read()
icon_src = f"data:{'image/png'};base64,{base64.b64encode(icon_data).decode()}"
config = AdminTableConfig(
    name="Simple Admin Table example",
    dashboard=lambda u: f"# Dashboard\n\nWelcome {u.email} to Simple Example of TableAPI\n\n"
    f"Checkout input form at [test_form](./#forms/test_form?field1=prefilled%20value)\n\n",
    icon_src=icon_src,
    version="dev",
    resources=[
        Resource(
            navigation="Users",
            name="User",
            display="All Users",
            resolver=SQLAlchemyResolver(
                SessionLocal,
                User,
                extra_cols={
                    "item_count": Query(func.count()).select_from(Item).filter(Item.owner_id == User.id),
                    "topic_value": literal("some/topic/value"),
                    "initial_topic_value": Query(func.abs(func.random() % 100)),
                },
            ),
            views=ResourceViews(
                list=ListView(
                    description="List of all users",
                    default_sort=("email", "desc"),
                    fields=[
                        # "id", id added automatically, because detail view is enabled
                        "email",
                        ("Active", "Active Filed description information", User.is_active),
                        ("Items", "item_count"),
                        ("Items Link", LinkTable("item_count", "Items", "owner_id", "eq", "id")),
                        (
                            "[[json]]JSON Field",
                            "This field will show formated JSON data",
                            lambda d: '{"key": "value", "key2": "value2", "sub": {"key": "value"}}',
                        ),
                    ],
                ),
                detail=DetailView(
                    title='Details of user "${email}"',
                    description=lambda d: f"Details of user {d.get('email', '')}",
                    fields=[
                        # "id", id added automatically, because detail view is enabled
                        "email",
                        ("Active", User.is_active),
                        ("Items", "item_count"),
                        ("Items Link", LinkTable("item_count", "Items", "owner_id", "eq", "id")),
                        ("Created At", User.created_at),
                        (
                            "Custom Field",
                            "This field has been computed",
                            lambda d: (f"Custom field with email: {d.get('email', '')}" * 10 + "\n") * 20,
                        ),
                        (
                            "[[html]]HTML Field",
                            "This filed will open popup with rendered html content",
                            lambda d: f'<h2>Title</h2><ul>{'\n'.join(f'<li> Item {x}</li>' for x in range(10))}</ul>',
                        ),
                        (
                            "[[markdown]]Markdown Field",
                            "This filed will open popup with rendered html content",
                            lambda d: f'## Custom Markdown Field\n\n {'\n'.join(f' - Item: {x}' for x in range(10))}',
                        ),
                        (
                            "[[json]]JSON Field",
                            "This field will show formated JSON data",
                            lambda d: '{"key": "value", "key2": "value2", "sub": {"key": "value"}}',
                        ),
                        (
                            "[[json]]Another JSON Field",
                            "This field will show formated JSON data",
                            lambda d: {"key": "value", "key2": "value2", "sub": {"key": "value"}},
                        ),
                        (
                            "Live Value",
                            "This field is automatically updated using the LiveDataManager",
                            LiveValue("topic_value", "initial_topic_value", history=True),
                        ),
                        (
                            "Custom link",
                            lambda d: {
                                "type": "link",
                                "kind": "table",
                                "resource": "Items",
                                "value": "Custom link to my items",
                                "filter": {"col": "owner_id", "op": "eq", "val": d["id"]},
                            },
                        ),
                    ],
                    actions=[custom_user_action, another_action, hello, create_item],
                    tables=[SubTable("Items", "Items", "owner_id", "eq", "id")],
                    graphs=[random_graph_data],
                ),
                create=CreateView(
                    schema=create_model(
                        "CreateUser", email=(str, Field(..., title="user email")), username=(str, Field(...))
                    ),
                    callback=create_user_function,
                ),
            ),
        ),
        Resource(
            navigation="Users",
            name="Items",
            hidden=True,
            resolver=SQLAlchemyResolver(
                SessionLocal,
                Item,
                extra_cols={
                    "owner_email": Query(User.email).filter(User.id == Item.owner_id),
                },
            ),
            views=ResourceViews(
                list=ListView(
                    fields=[
                        "id",
                        Item.title,
                        ("Is Public", Item.public),
                        ("Description", Item.description),
                        ("Owner", LinkDetail("owner_email", "User", "owner_id")),
                    ],
                ),
            ),
        ),
        Resource(
            navigation="Users",
            name="Public Items",
            resolver=SQLAlchemyResolver(
                SessionLocal,
                Item,
                extra_cols={
                    "owner_email": Query(User.email).filter(User.id == Item.owner_id),
                },
            ),
            views=ResourceViews(
                list=ListView(
                    description=generate_item_list_description,
                    hidden_filters=[ResolverBase.AppliedFilter("public", "eq", "true")],
                    fields=[
                        "id",
                        Item.title,
                        ("Is Public", Item.public),
                        ("Description", Item.description),
                        ("Owner", LinkDetail("owner_email", "User", "owner_id")),
                    ],
                ),
            ),
        ),
    ],
    pages=[
        Page(
            name="Custom HTML page",
            navigation="Custom Pages",
            content=lambda request: "<h1>Dashboard</h1><p>Welcome to the custom html page</p>",
            type="html",
        ),
        Page(
            public=True,
            name="Custom Markdown page",
            navigation="Custom Pages",
            content=lambda request: "# Dashboard\n\nWelcome to the markdown page",
            type="markdown",
        ),
        Page(
            name="Iframe page",
            navigation="Custom Pages",
            content='<iframe src="https://www.google.com" style="width: 100%; height: 100%; border: none;"></iframe>',
            type="html",
        ),
    ],
    navigation_icons={
        "Users": "user",
        "Custom Pages": "book",
    },
    input_forms=[
        InputForm(
            public=True,
            location="test_form",
            title="Public form",
            description=lambda: "> Form description in markdown format",
            schema=create_model(
                "Public form",
                field1=(str, Field(title="String Field")),
                integer_value=(int, Field(title="Integer Field")),
                hidden_field=(
                    str,
                    Field("secret value", json_schema_extra={"format": "hidden"}),
                ),
            ),
            callback=lambda model: print("Public form called: ", model),
        ),
        InputForm(
            public=False,
            location="test_form_private",
            title="Private form",
            description=lambda: "This form should be visible only to logged-in users",
            schema=create_model(
                "Private form",
                field1=(str, Field(title="String Field")),
            ),
            callback=lambda model: "Successfully submitted form with data: " + json.dumps(model.dict()),
        ),
    ],
    live_data_manager=LiveDataProducer,
)


# generate models and insert some data
Base.metadata.create_all(bind=engine)

with SessionLocal() as session:
    session.add(u1 := User(email=f"{random.randint(10, 10**10)}@email.local"))
    session.add(u2 := User(email=f"{random.randint(10, 10**10)}@email.local"))
    session.flush()
    session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u1.id))
    session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u1.id, public=False))
    session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u1.id, public=False))
    session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u2.id))
    session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u2.id))
    session.add(Item(title=f"item {random.randint(10, 10**10)}", owner_id=u2.id))
    session.add(Item(title=f"item {random.randint(10, 10**10)}"))
    session.add(Item(title=f"item {random.randint(10, 10**10)}"))
    session.add(Item(title=f"other item {random.randint(10, 10**10)}", owner_id=u2.id, public=False))
    session.commit()


at = AdminTable(config=config)

app = FastAPI()
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/api/admin", FastAPIWrapper(at))
app.get("/")(lambda: RedirectResponse("/api/admin/", status_code=status.HTTP_307_TEMPORARY_REDIRECT))

if __name__ == "__main__":
    uvicorn.run("example.fastapi_simple:app", reload_dirs="./", reload=True)
