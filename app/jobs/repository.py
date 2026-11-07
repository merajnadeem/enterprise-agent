import json

from uuid import uuid4

from app.jobs.idempotency import request_hash


class IdempotencyConflict(Exception):
    pass


async def create_investigation_job(
    connection,
    *,
    tenant_id: str,
    user_id: str,
    idempotency_key: str,
    question: str,
    sources: list[str],
    require_human_approval: bool,
):

    payload = {
        "question": question,
        "sources": sorted(set(sources)),
        "require_human_approval": require_human_approval
    }

    digest = request_hash(payload)

    async with connection.transaction():
        proposed_job_id = uuid4

        row = await connection.fetchrow(
            """
            INSERT INTO investigation_jobs (
                id,
                tenant_id,
                user_id,
                idempotency_key,
                request_hash,
                question,
                requested_sources,
                require_human_approval,
                status
            )

            VALUES (
                $1, $2, $3, $4, $5, $6,
                $7::jsonb, $8, 'pending'
            )

            ON CONFLICT (
                tenant_id,
                idempotency_key
            )
            DO NOTHING

            RETURNING id, status, created_at, request_hash
            """,

            proposed_job_id,
            tenant_id,
            user_id,
            idempotency_key,
            digest,
            question,
            json.dumps(payload["sources"]),
            require_human_approval,
        )