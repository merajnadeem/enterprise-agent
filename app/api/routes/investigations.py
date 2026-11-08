from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)

from app.api.schemas import (
    InvestigationRequest,
    InvestigationResponse,
)

from app.security.context import SecurityContext

from app.security.dependencies import (
    get_security_context,
    require_permission,
)

from app.jobs.repository import (
    create_investigation_job,
    IdempotencyConflict,
)

from uuid import UUID

from app.api.schemas import (
    InvestigationStatusResponse,
)


router = APIRouter(
    prefix="/api/v1/investigations",
    tags=["investigations"],
)

@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_investigation(
    payload: InvestigationRequest,
    request: Request,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=8, max_length=128),
    ],
    security_context: Annotated[
        SecurityContext,
        Depends(get_security_context),
    ],
):

    require_permission(
        security_context,
        "investigation:create",
    )

    principal = security_context.principal

    pool = request.app.state.db_pool

    async with pool.acquire() as connection:

        try:

            result = await create_investigation_job(
                connection,
                tenant_id=principal.tenant_id,
                user_id=principal.user_id,
                idempotency_key=idempotency_key,
                question=payload.question,
                sources=payload.sources,
                require_human_approval=(
                    payload.require_human_approval
                ),
            )

        except IdempotencyConflict as exc:

            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

    return InvestigationResponse(
        job_id=result["job_id"],
        status=result["status"],
        message=(
            "Investigation accepted."
            if result["created"]
            else "Existing investigation returned."
        ),
    )



@router.get("/{job_id}")
async def get_investigation_status(
    job_id: UUID,
    request: Request,
    security_context: Annotated[
        SecurityContext,
        Depends(get_security_context),
    ],
):

    require_permission(
        security_context,
        "investigation:read",
    )

    pool = request.app.state.db_pool

    async with pool.acquire() as connection:

        row = await connection.fetchrow(
            """
            SELECT
                id,
                status,
                created_at

            FROM investigation_jobs

            WHERE id = $1
              AND tenant_id = $2
              AND user_id = $3
            """,
            job_id,
            security_context.principal.tenant_id,
        )

    if row is None:

        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    return InvestigationStatusResponse(
        job_id=str(row["id"]),
        status=row["status"],
        created_at=row["created_at"].isoformat(),
    )