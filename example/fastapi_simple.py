import base64
import json
import os.path
import random
from datetime import datetime, timedelta
from typing import Annotated, Optional

import uvicorn
from base import Base, SessionLocal, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Item, User
from pydantic import Field, create_model
from sqlalchemy import func
from sqlalchemy.orm import Query
from starlette import status
from starlette.responses import RedirectResponse
from typing_extensions import Doc

from admin_table import AdminTable, AdminTableConfig, Resource, ResourceViews
from admin_table.config import (
    CreateView,
    DetailView,
    LineGraphData,
    LinkDetail,
    LinkTable,
    ListView,
    Page,
    SubTable,
)
from admin_table.modules import SQLAlchemyResolver
from admin_table.modules.bases import ResolverBase
from admin_table.wrappers import FastAPIWrapper


def custom_user_action(
    user: User, string_param: Annotated[str, Doc("first param of the method")], int_param: int, bool_param: bool
) -> str:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    return f"performed action on {user} with params: {string_param}, {int_param}, {bool_param}"


def another_action(user: User, bool_param: bool) -> str:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    return f"performed action on {user} {bool_param}"


def hello(user: User, b1: bool, b2: bool, string1: str, string2: str, string3: str) -> str:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    raise Exception("World")


def random_graph_data(
    user: User, range_from: Optional[datetime] = None, range_to: Optional[datetime] = None
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


icon_data = open(os.path.join(os.path.dirname(__file__), "icon.png"), "rb").read()
icon_src = f"data:{'image/png'};base64,{base64.b64encode(icon_data).decode()}"
config = AdminTableConfig(
    name="Simple Admin Table example",
    dashboard=lambda u: f"# Dashboard\n\nWelcome {u.email} to Simple Example of TableAPI",
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
                    ],
                    actions=[custom_user_action, another_action, hello],
                    tables=[SubTable("Items", "Items", "owner_id", "eq", "id")],
                    graphs=[random_graph_data],
                ),
                create=CreateView(
                    schema=create_model(
                        "CreateUser", email=(str, Field(..., description="user email")), username=(str, Field(...))
                    ),
                    callback=lambda user: print("Creating user", user),
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
)

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
