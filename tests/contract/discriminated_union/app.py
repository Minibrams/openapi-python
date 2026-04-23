from __future__ import annotations

from typing import Annotated, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class Cat(BaseModel):
    pet_type: Literal["cat"]
    lives: int


class Dog(BaseModel):
    pet_type: Literal["dog"]
    bark_volume: int


Pet = Annotated[Cat | Dog, Field(discriminator="pet_type")]


class PetEnvelope(BaseModel):
    pet: Pet
    request_id: str


@app.get("/pets/{pet_id}", response_model=PetEnvelope)
def get_pet(pet_id: int) -> PetEnvelope:
    return PetEnvelope(pet=Cat(pet_type="cat", lives=9), request_id=f"pet_{pet_id}")


@app.post("/pets", response_model=PetEnvelope)
def create_pet(body: PetEnvelope) -> PetEnvelope:
    return body
