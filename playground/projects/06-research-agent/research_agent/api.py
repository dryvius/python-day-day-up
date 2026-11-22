from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, status

from research_agent.core import (
    IdempotencyConflict,
    JobNotFound,
    JobRunner,
    JobStore,
    build_services,
)
from research_agent.models import CreateJobRequest, NamespaceRequest


def _services(request: Request) -> tuple[JobStore, JobRunner]:
    return request.app.state.store, request.app.state.runner


def create_app() -> FastAPI:
    store, runner = build_services()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.store = store
        app.state.runner = runner
        await runner.start()
        try:
            yield
        finally:
            await runner.stop()

    app = FastAPI(title="Research Agent", version="1.0.0", lifespan=lifespan)

    @app.post("/v1/jobs", status_code=status.HTTP_202_ACCEPTED)
    async def create_job(payload: CreateJobRequest, request: Request) -> dict[str, Any]:
        active_store, active_runner = _services(request)
        try:
            job, replayed = active_store.create(payload)
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from exc
        if not replayed:
            await active_runner.enqueue(job)
        response = job.to_public()
        response["idempotent_replay"] = replayed
        return response

    @app.get("/v1/jobs/{job_id}")
    async def get_job(
        job_id: str,
        request: Request,
        namespace: str = Query(pattern=r"^[a-zA-Z0-9_-]{1,64}$"),
    ) -> dict[str, Any]:
        active_store, _ = _services(request)
        try:
            return active_store.get(job_id, namespace).to_public()
        except JobNotFound as exc:
            raise HTTPException(status_code=404, detail="job_not_found") from exc

    @app.post("/v1/jobs/{job_id}/approve", status_code=status.HTTP_202_ACCEPTED)
    async def approve_job(
        job_id: str,
        payload: NamespaceRequest,
        request: Request,
    ) -> dict[str, Any]:
        _, active_runner = _services(request)
        try:
            job = await active_runner.approve(job_id, payload.namespace)
            return job.to_public()
        except JobNotFound as exc:
            raise HTTPException(status_code=404, detail="job_not_found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/v1/jobs/{job_id}/revoke")
    async def revoke_job(
        job_id: str,
        payload: NamespaceRequest,
        request: Request,
    ) -> dict[str, Any]:
        active_store, _ = _services(request)
        try:
            return active_store.revoke(job_id, payload.namespace).to_public()
        except JobNotFound as exc:
            raise HTTPException(status_code=404, detail="job_not_found") from exc

    @app.post("/v1/namespaces/{namespace}/revoke")
    async def revoke_namespace(namespace: str, request: Request) -> dict[str, Any]:
        active_store, _ = _services(request)
        return {"namespace": namespace, "revoked_jobs": active_store.revoke_namespace(namespace)}

    @app.delete("/v1/namespaces/{namespace}/expired")
    async def purge_expired(namespace: str, request: Request) -> dict[str, Any]:
        active_store, _ = _services(request)
        return {
            "namespace": namespace,
            "purged_jobs": active_store.purge_expired(namespace),
            "purged_notes": active_store.memory.purge_before(namespace, datetime.now(UTC)),
        }

    return app


app = create_app()
