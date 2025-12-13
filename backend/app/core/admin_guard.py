from fastapi import Header, HTTPException

def require_admin(x_role: str | None = Header(default=None, alias="X-Role")) -> None:
    if x_role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only. Set header X-Role: ADMIN")
