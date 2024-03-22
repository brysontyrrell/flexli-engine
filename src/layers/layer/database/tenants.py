from pydantic import BaseModel, Extra


class User(BaseModel):
    sub: str
    tenant_id: str

    class Config:
        extra = Extra.ignore


def write_user_context(table_resource, user: User):
    item = {"pk": f"U#{user.sub}", "sk": "A", **user.dict}
    table_resource.put_item(Item=item)


def get_user_context(table_resource, sub: str) -> User:
    response = table_resource.get_item(Key={"pk": f"U#{sub}", "sk": "A"})
    return User(**response["Item"])
