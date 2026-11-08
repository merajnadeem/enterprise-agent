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
                user_id,
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

        if row:

            await connection.execute(
                """
                INSERT INTO outbox_events (
                    job_id,
                    event_type,
                    payload
                )

                VALUES (
                    $1,
                    'investigation.requested',
                    $2::jsonb
                )
                """,
                proposed_job_id,
                json.dumps({
                    "job_id": str(proposed_job_id)
                }),
            )

            return {
                "job_id": str(proposed_job_id),
                "status": "pending",
                "created": True,
            }

        existing = await connection.fetchrow(
            """
            SELECT id, request_hash, status
            FROM investigation_jobs
            WHERE tenant_id = $1
              AND user_id = $2
              AND idempotency_key = $3
            """,
            tenant_id,
            idempotency_key,
        )

        if existing["request_hash"] != digest:

            raise IdempotencyConflict(
                "Idempotency key reused with a different request."
            )

        return {
            "job_id": str(existing["id"]),
            "status": existing["status"],
            "created": False,
        }
