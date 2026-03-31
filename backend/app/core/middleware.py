from starlette.middleware.base import BaseHTTPMiddleware

class CookieToAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = request.cookies.get("uniforma_admin_access_token")

        if token:
            request.headers.__dict__["_list"].append(
                (b"authorization", f"Bearer {token}".encode())
            )

        return await call_next(request)
