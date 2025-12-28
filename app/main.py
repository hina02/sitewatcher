import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from arq.jobs import Job, JobStatus
from fastapi import Depends, FastAPI, Request
from prometheus_client import make_asgi_app
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s",
)

logger = logging.getLogger(__name__)


sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Error Monitoring(Default: Enabled)
        send_default_pii=True,
        # Enable sending logs to Sentry
        enable_logs=True,
        # Enable Tracing
        traces_sample_rate=1.0,
        # Enable Performance Monitoring
        profile_session_sample_rate=0.0,
        profile_lifecycle="trace",
    )
    sentry_sdk.set_tag("service", "api")
else:
    logger.warning("SENTRY_DSN is not set. Sentry is disabled.")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 16379))


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: dict | None = None
    error: str | None = None


async def get_redis(request: Request) -> ArqRedis:
    return request.app.state.arq_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = await create_pool(
        RedisSettings(host=REDIS_HOST, port=REDIS_PORT, database=1)
    )
    app.state.arq_redis = redis

    yield

    await redis.aclose()


app = FastAPI(lifespan=lifespan)

metrics = make_asgi_app()
app.mount("/metrics", metrics)


@app.post("/jobs")
async def create_job(url: str, redis: ArqRedis = Depends(get_redis)) -> dict:
    job = await redis.enqueue_job("http_request", url)
    status = await job.status()
    return {"job_id": job.job_id, "status": status}


@app.get("/jobs/{job_id}")
async def get_task(job_id: str, redis: ArqRedis = Depends(get_redis)) -> JobResponse:
    job = Job(job_id, redis)
    status = await job.status()
    if status.complete:
        result = await job.result()
        return JobResponse(job_id=job_id, status=status, result=result)
    else:
        return JobResponse(job_id=job_id, status=status)


@app.get("/jobs/pending")
async def list_pending_jobs(redis: ArqRedis = Depends(get_redis)) -> dict:
    jobs = await redis.queued_jobs()

    safe_jobs = []
    for job in jobs:
        safe_jobs.append(
            {
                "job_id": job.job_id,
                "function": job.function,
                "args": job.args,
                "kwargs": job.kwargs,
                "enqueue_time": job.enqueue_time,
                "score": job.score,  # 実行予定スコア
            }
        )

    return {"pending_jobs": safe_jobs}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
