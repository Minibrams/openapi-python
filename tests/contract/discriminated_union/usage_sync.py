from __future__ import annotations

from typing import Literal, assert_type

from generated.my_client import Client
from generated.my_client.types import Cat, Dog, PetEnvelope

client = Client(base_url="http://testserver")

cat: Cat = {"pet_type": "cat", "lives": 9}
dog: Dog = {"pet_type": "dog", "bark_volume": 4}
assert_type(cat["pet_type"], Literal["cat"])
assert_type(dog["pet_type"], Literal["dog"])

cat_body: PetEnvelope = {"pet": cat, "request_id": "req_cat"}
dog_body: PetEnvelope = {"pet": dog, "request_id": "req_dog"}

cat_result = client.post("/pets")(body=cat_body)
assert_type(cat_result, PetEnvelope)
assert_type(cat_result["pet"], Cat | Dog)
assert_type(cat_result["request_id"], str)

dog_result = client.post("/pets")(body=dog_body)
assert_type(dog_result, PetEnvelope)
assert_type(dog_result["pet"], Cat | Dog)

fetched = client.get("/pets/{pet_id}")(params={"pet_id": 1})
assert_type(fetched, PetEnvelope)
assert_type(fetched["pet"], Cat | Dog)
