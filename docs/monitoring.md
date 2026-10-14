# Monitoring demonstration

Compose starts Prometheus at http://localhost:9090 on the deployment machine. Open **Status / Target health** (or `/targets`) and verify `taskflow` is UP. Metrics are scraped every five seconds. Open `/query` to graph these PromQL expressions:

| What you show | Query |
| --- | --- |
| Application scrape availability | `up{job="taskflow"}` |
| Total responses by status | `sum by (status) (taskflow_http_requests_total)` |
| Requests per second | `sum(rate(taskflow_http_requests_total[1m]))` |
| Server errors per second | `sum(rate(taskflow_http_requests_total{status=~"5.."}[1m])) or vector(0)` |
| Mean response time in seconds | `sum(rate(taskflow_http_request_duration_seconds_sum[1m])) / sum(rate(taskflow_http_request_duration_seconds_count[1m]))` |

Generate activity by running `scripts/smoke.py` a few times. Allow at least one minute of scrapes for rate graphs. Health-check traffic is included. Route labels use templates rather than task IDs to keep the number of metric series bounded.

## Incident and recovery

Run these commands on the Jenkins deployment agent:

```sh
docker compose -p taskflow-demo stop api
# Wait approximately 45 seconds, then view Prometheus /alerts.
docker compose -p taskflow-demo start api
```

Capture `TaskFlowUnavailable` firing, then resolving after restart. For a manual deployment omit `-p taskflow-demo`. Data stays in the DynamoDB volume. The alert is visible in Prometheus only; email/Slack delivery is not configured. `up` tests the metrics endpoint, while `/health` checks DynamoDB connectivity. Database failures produce HTTP 503 from the health endpoint and contribute to the server-error alert.

This demo runs a single Gunicorn worker so process-local metrics are consistent. Multiple workers require Prometheus multiprocess configuration. Prometheus itself has persistent storage but is not highly available.

Teacher evidence: screenshot of UP target, request/status graph, latency graph, firing alert and recovered target. This completes the monitoring stage; a green build alone is not proof the application stays healthy.
