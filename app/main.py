import mimetypes

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router

# The slim Docker image has no /etc/mime.types so webp is unknown by default.
mimetypes.add_type("image/webp", ".webp")

app = FastAPI()

app.include_router(api_router)

# Serve locally stored product images at /uploads/
# local_path values like /uploads/products/filename.webp map to this mount.
# The storage volume is mounted at /opt/uniforma/storage in production.
app.mount(
    "/uploads",
    StaticFiles(directory="/opt/uniforma/storage/uploads"),
    name="uploads",
)
