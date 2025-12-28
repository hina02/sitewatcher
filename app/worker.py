import logging
import os
import time

import httpx
import sentry_sdk
from arq.connections import RedisSettings
from prometheus_client import start_http_server

from app.metrics import CHECK_DURATION, JOB_COUNT

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
    sentry_sdk.set_tag("service", "worker")
else:
    logger.warning("SENTRY_DSN is not set. Sentry is disabled.")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 16379))


async def startup(ctx):
    # Worker起動時にPrometheusサーバーを別スレッドで立ち上げる
    start_http_server(8001, addr="0.0.0.0")
    logger.info("Prometheus metrics server started on port 8001")


async def http_request(ctx, url: str) -> dict:
    # HTTPリクエスト
    with CHECK_DURATION.labels(url=url).time():
        try:
            start_time = time.perf_counter()
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=1.0)
                response.raise_for_status()
            end_time = time.perf_counter()
            duration = end_time - start_time
            status_code = response.status_code
            logger.info(f"Request to {url} took {duration:.2f} seconds.")
            logger.info(f"Status code: {status_code}")
            JOB_COUNT.labels(status="success").inc()
            return {
                "contents": response.text,
                "duration": duration,
                "status": "completed",
                "status_code": status_code,
            }
        except httpx.TimeoutException as exc:
            JOB_COUNT.labels(status="failure").inc()
            raise exc
        except httpx.HTTPStatusError as exc:
            JOB_COUNT.labels(status="failure").inc()
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
        except httpx.RequestError as exc:
            JOB_COUNT.labels(status="failure").inc()
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise exc


class WorkerSettings:
    functions = [http_request]
    on_startup = startup
    redis_settings = RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        database=1,
        conn_timeout=10,
        conn_retries=5,
        conn_retry_delay=1,
    )
    max_jobs = 10
