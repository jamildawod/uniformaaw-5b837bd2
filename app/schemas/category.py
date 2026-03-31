from pydantic import BaseModel, ConfigDict


class CategoryListItem(BaseModel):
    id: int
    name: str
    slug: str
    image: str | None = None
    parent_id: int | None = None
    sector_slug: str | None = None  # which ?sector= param to use for product filtering

    model_config = ConfigDict(from_attributes=True)
