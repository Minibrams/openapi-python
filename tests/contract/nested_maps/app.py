from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    sku: str
    quantity: int


class Shelf(BaseModel):
    label: str
    items: list[Item]


class Warehouse(BaseModel):
    id: int
    shelves: list[Shelf]
    inventory_by_sku: dict[str, Item]
    metadata: dict[str, str]


@app.get("/warehouses/{warehouse_id}", response_model=Warehouse)
def get_warehouse(warehouse_id: int) -> Warehouse:
    item = Item(sku="abc", quantity=2)
    return Warehouse(
        id=warehouse_id,
        shelves=[Shelf(label="A", items=[item])],
        inventory_by_sku={item.sku: item},
        metadata={"region": "north"},
    )
