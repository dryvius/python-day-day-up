"""Authentication dependencies."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from todo_api.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    supplied_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if supplied_key is None or not secrets.compare_digest(supplied_key, settings.app_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或缺失的 API Key",
        )
