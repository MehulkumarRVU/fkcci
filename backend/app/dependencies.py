from typing import Callable, List
from fastapi import Depends, HTTPException, status

from .routes.auth import get_current_athlete


def require_role(*allowed_roles: List[str]) -> Callable:
    async def role_checker(current_athlete = Depends(get_current_athlete)):
        if current_athlete.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_athlete

    return role_checker
