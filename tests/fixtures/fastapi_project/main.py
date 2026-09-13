from fastapi import FastAPI, Query, Body
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/users/{user_id}")
def get_user(user_id: int, q: str = Query(None)):
    return {"user_id": user_id, "q": q}

@app.post("/items/")
def create_item(item: Item, user_id: int = Body(...)) -> Item:
    return item
