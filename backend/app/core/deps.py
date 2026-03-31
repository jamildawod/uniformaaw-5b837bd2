from fastapi import HTTPException, Request, status

def get_current_admin(request: Request):
    token = request.cookies.get("uniforma_admin_access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # ✅ INGEN decode (vi bryr oss bara om att cookie finns)
    return {"token": token}
