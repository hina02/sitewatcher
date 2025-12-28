from prometheus_client import Counter, Gauge, Histogram

JOB_COUNT = Counter(
    "sitewatcher_job_total", "Total number of jobs processed by SiteWatcher", ["status"]
)

CHECK_DURATION = Histogram(
    "sitewatcher_check_duration_seconds", "Time spent checking the website", ["url"]
)
