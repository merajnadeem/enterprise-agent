from fastapi import Request, HTTPException, status

from app.security.context import SecurityContext


async def get_security_context(request: Request) -> SecurityContext:

    context = getattr(request.state, "security_context", None)

    if not isinstance(context, SecurityContext):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    return context


def require_permission(context: SecurityContext, permission: str):

    if permission not in context.principal.permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
