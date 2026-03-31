from fastapi import Response

def apply_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="uniforma_admin_access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/"
    )
