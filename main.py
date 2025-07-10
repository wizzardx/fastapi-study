from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


class User(BaseModel):
    username: str
    email: str
    full_name: str = None


# In-memory databases:
items: list[Item] = []
users: list[User] = []


# Misc endpoints:

@app.get("/")
async def get_root():
    return {"message": "hello world"}


@app.get("/search")
async def search(q: str):
    return {"q": q}

# Item endpoints:

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id}


@app.post("/items")
async def item_post(item: Item):
    items.append(item)
    return {"message": "Item created", "item": item}


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    items[item_id] = item  # Fixed: removed the + 1
    return {"message": "Item updated", "item": item}


# User endpoints:
@app.post("/users/")
async def create_user(user: User):
    users.append(user)
    return {"message": "User created", "user": user}

