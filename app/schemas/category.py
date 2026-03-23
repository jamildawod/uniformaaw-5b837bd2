from pydantic import BaseModel, ConfigDict


class CategoryListItem(BaseModel):
    id: int
    name: str
    slug: str
    image: str | None = None
    parent_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
