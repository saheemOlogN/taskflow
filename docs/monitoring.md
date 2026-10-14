# Monitoring demonstration

The native launcher starts Prometheus at http://localhost:9090 on the deployment machine. Open **Status / Target health** (or `/targets`) and verify `taskflow` is UP. Metrics are scraped every five seconds. Open `/query` to graph these PromQL expressions:

| What you show | Query |
| --- | --- |
| Application scrape availability | `up{job="taskflow"}` |
| Total responses by status | `sum by (status) (taskflow_http_requests_total)` |
| Requests per second | `sum(rate(taskflow_http_requests_total[1m]))` |
| Server errors per second | `sum(rate(taskflow_http_requests_total{status=~"5.."}[1m])) or vector(0)` |
| Mean response time in seconds | `sum(rate(taskflow_http_request_duration_seconds_sum[1m])) / sum(rate(taskflow_http_request_duration_seconds_count[1m]))` |

Generate activity by running `scripts/smoke.py` a few times. Allow at least one minute of scrapes for rate graphs. Route labels use templates rather than task IDs to keep the number of metric series bounded. Each metrics scrape also checks DynamoDB; graph `taskflow_database_up` to see database availability. A separate database-down alert fires after 30 seconds.

## Incident and recovery

Run these commands on the Jenkins deployment agent:

```powershell
.\.venv\Scripts\python.exe scripts/native.py stop-api
# Wait approximately 45 seconds, then view Prometheus /alerts.
.\.venv\Scripts\python.exe scripts/native.py start
```

Capture `TaskFlowUnavailable` firing, then resolving after restart. Run these commands from the deployed project workspace. Data stays in `.runtime/data`. The alert is visible in Prometheus only; email/Slack delivery is not configured. `up` tests the metrics endpoint, while `/health` checks DynamoDB connectivity. Database failures produce HTTP 503 from the health endpoint and contribute to the server-error alert.

This demo runs a single Waitress process so process-local metrics are consistent. Multiple workers require Prometheus multiprocess configuration. Prometheus itself has persistent storage but is not highly available.

Teacher evidence: screenshot of UP target, request/status graph, latency graph, firing alert and recovered target. This completes the monitoring stage; a green build alone is not proof the application stays healthy.
