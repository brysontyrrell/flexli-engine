from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sub: str
    tenant_id: str


def write_user_context(table_resource, user: User):
    item = {"pk": f"U#{user.sub}", "sk": "A", **user.dict}
    table_resource.put_item(Item=item)


def get_user_context(table_resource, sub: str) -> User:
    response = table_resource.get_item(Key={"pk": f"U#{sub}", "sk": "A"})
    return User(**response["Item"])
