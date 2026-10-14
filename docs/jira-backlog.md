# Jira backlog

Create these as tasks; numbers below are examples, not existing Jira tickets.

| Example key | Task | Acceptance evidence |
| --- | --- | --- |
| DEVOPS-1 | Create DynamoDB task API | Create/list/complete/delete a task; show stored data |
| DEVOPS-2 | Validate task input | Empty and oversized titles rejected with HTTP 400; automated tests pass |
| DEVOPS-3 | Containerize API and database | Compose starts both; task survives restart |
| DEVOPS-4 | Add GitHub CI | PR shows tests and deployed integration check passing |
| DEVOPS-5 | Deploy using Jenkins | Pipeline stages and JUnit report visible; smoke test passes |
| DEVOPS-6 | Demonstrate failure and recovery | Failing test blocks deployment; corrected change succeeds |
| DEVOPS-7 | Monitor deployment using Prometheus | UP target, request and latency metrics, firing and resolved outage alert |

Suggested next genuine change: restrict task titles to 80 characters. First update the boundary tests and observe failure, then update validation and error text, get a green PR, merge, and watch Jenkins deploy. Use a new Jira ticket and its actual issue key for this exercise. Keep evidence of the real work instead of inventing historical activity.
