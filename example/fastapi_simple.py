import random
from typing import Annotated

import uvicorn
from base import Base, SessionLocal, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Item, User
from pydantic import Field, create_model
from sqlalchemy import func, insert
from sqlalchemy.orm import Query
from starlette import status
from starlette.responses import RedirectResponse
from typing_extensions import Doc

from admin_table import AdminTable, AdminTableConfig, Resource, ResourceViews
from admin_table.config import CreateView, DetailView, LinkDetail, LinkTable, ListView, Page, SubTable
from admin_table.modules.sqlalchemy import SQLAlchemyResolver
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


def hello(user: User, b1: bool, b2: bool, string1: str, string2: str, strin3: str) -> str:
    """
    Performs various actions on the user :wink:
    Try to pass "hello" into the `string_param` and see what happens
    """
    raise Exception("World")


config = AdminTableConfig(
    name="Simple TableAPI example",
    dashboard=lambda u: f"# Dashboard\n\nWelcome {u.email} to Simple Example of TableAPI",
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
                    fields=[
                        # "id", id added automatically, because detail view is enabled
                        "email",
                        ("Active", User.is_active),
                        ("Items", "item_count"),
                        ("Items Link", LinkTable("item_count", "Items", "owner_id", "eq", "id")),
                    ],
                ),
                detail=DetailView(
                    title='Details of user "${email}"',
                    fields=[
                        # "id", id added automatically, because detail view is enabled
                        "email",
                        ("Active", User.is_active),
                        ("Items", "item_count"),
                        ("Items Link", LinkTable("item_count", "Items", "owner_id", "eq", "id")),
                        (
                            "CustomField",
                            "This field has been computed",
                            lambda d: f"Custom field with email: {d.get('email', '')}",
                        ),
                    ],
                    actions=[custom_user_action, another_action, hello],
                    tables=[SubTable("Items", "Items", "owner_id", "eq", "id")],
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
    ],
)

Base.metadata.create_all(bind=engine)

with SessionLocal() as session:
    session.execute(insert(User).values(email=f"{random.randint(10, 10**10)}@email.local"))
    session.execute(insert(User).values(email=f"{random.randint(10, 10**10)}@email.local"))
    session.execute(insert(Item).values(title=f"item ...{random.randint(10, 10**10)}", owner_id=1))
    session.execute(insert(Item).values(title=f"some item - {random.randint(10, 10**10)}", owner_id=2))
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
