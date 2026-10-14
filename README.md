# TaskFlow: end-to-end DevOps without Docker

A small Python task API with DynamoDB storage. Runs directly on Windows: no Docker, WSL or virtual machine required.

**Jira planning → GitHub commit/PR → automated tests → ZIP build → Jenkins deployment → Prometheus monitoring**

## Start on this computer

Python and Java 21 are already installed. Run in PowerShell:

```powershell
cd C:\Users\Saheem\OneDrive\Desktop\asd
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/native.py setup
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/native.py build
.\.venv\Scripts\python.exe scripts/native.py deploy
```

Setup downloads AWS DynamoDB Local and Prometheus for Windows, verifies their published SHA-256 checksums, and keeps them inside `.tools`. Deployment starts background processes without opening extra windows, creates the database table, runs a CRUD smoke test and verifies Prometheus reports the app UP. Downloads are needed only on first setup. On another machine, set JAVA_HOME to its installed Java 17+ directory.

Open:

- API health: http://localhost:5000/health
- Tasks: http://localhost:5000/tasks
- Prometheus targets: http://localhost:9090/targets
- Monitoring graphs: http://localhost:9090/query
- Alerts: http://localhost:9090/alerts

Create and update a task:

```powershell
$task = Invoke-RestMethod http://localhost:5000/tasks -Method Post -ContentType 'application/json' -Body '{"title":"Demonstrate my DevOps pipeline"}'
Invoke-RestMethod http://localhost:5000/tasks
Invoke-RestMethod "http://localhost:5000/tasks/$($task.id)" -Method Patch -ContentType 'application/json' -Body '{"done":true}'
```

Stop everything: `.\.venv\Scripts\python.exe scripts/native.py stop`.
Start the existing release again: `.\.venv\Scripts\python.exe scripts/native.py start`.
After code changes: run `build` then `deploy`. Data survives restarts in `.runtime/data`. Logs are `.runtime/*.log`; the ZIP artifact is `dist/taskflow.zip`; deployed code is `.runtime/release`. These directories are ignored by Git. Stop processes before moving/deleting this folder. Background processes do not automatically restart after reboot.

## GitHub

Push the changed project to your existing repository:

```powershell
git add .
git commit -m "Run DevOps pipeline natively on Windows without Docker"
git push
```

GitHub Actions now uses a Windows runner. It tests the API, builds and uploads a ZIP artifact, starts real DynamoDB Local and Prometheus, verifies CRUD and monitoring, then stops its temporary services. Open Actions and show the successful run and downloadable release artifact. No Docker installation is used by this workflow.

## Jenkins deployment on Windows

Install Jenkins LTS with a Java version supported by that Jenkins release; configure a Windows agent with label `windows`, Python 3.13, Git and Java 21+ as required. Install Pipeline, Git and JUnit plugins. Ensure the agent account can use Python and Java and has internet access for first setup. Set `JAVA_HOME` for that account or in the agent environment; your interactive PowerShell variable does not configure a Windows service.

Create a Pipeline job → Pipeline script from SCM → Git → your repository URL → branch `*/main` → script path `Jenkinsfile`. Add repository credentials in Jenkins only if needed. Run Build Now once; later changes to main are detected by SCM polling approximately every five minutes.

Stages: Checkout, Install, Test, Build, Prepare native tools, Deploy and monitor. Failed tests prevent deployment. Jenkins archives the release ZIP and JUnit report. The deployment extracts that ZIP to `.runtime/release`, runs Waitress, and verifies the API and Prometheus scrape. The demo services remain running after the build; the Jenkins process cookie is set explicitly for those background services.

Use one dedicated demo job/agent. Stop a manually started copy before running Jenkins on the same machine (ports 5000, 8000 and 9090 must be free). Do not delete/clean the Jenkins workspace while the demo runs. Stop it with `scripts/native.py stop` from that workspace using the same account. On a remote agent, localhost links refer to that agent computer.

This is deployment to a local Windows environment, not public cloud hosting. It has a brief restart during deploy and no automatic rollback. Revert a bad Git commit and rerun Jenkins to recover. The runtime currently shares the project's virtual environment; immutable environments and Windows services are future production improvements.

## Jira

Create a project with key DEVOPS and a To Do / In Progress / Done board. Add the tasks in `docs/jira-backlog.md`. Connect your repository through the GitHub for Atlassian integration (administrator access may be needed). Put the actual Jira issue key in branch names, commit messages and PR titles, for example `DEVOPS-2-title-validation`. Confirm that Jira displays the linked development activity. Status transitions are manual.

## Monitoring and presentation

Follow `docs/monitoring.md` for request counts, response times and outage alerts. Follow `docs/demo-guide.md` for the teacher demonstration. Capture genuine GitHub/Jenkins runs, Jira links, the running API, Prometheus graphs, and a firing/resolved alert. The stated assignment covers all stages from commit to deployment and monitoring; final acceptance depends on the teacher's assessment.

## DynamoDB Local versus AWS

This demo uses the official downloadable DynamoDB Local database with persistent storage and dummy credentials. It does not create an AWS cloud table or incur DynamoDB cloud usage. AWS provides the Java distribution as an alternative to Docker. If a real AWS table is required, configure an AWS profile, remove the local endpoint environment variable, and run `init_db.py` and `serve.py` directly with that profile. The native launcher intentionally always selects the local database. Never commit AWS secrets.

## Limits

The API has no authentication and Waitress/Prometheus bind to localhost. DynamoDB Local may bind on all interfaces; do not allow inbound public-network access through Windows Firewall. Use only a trusted classroom/local environment. Listing tasks scans the small demo table. Metrics live in one Python process. Alerts are visible in Prometheus; email/Slack notifications are not configured. Downloaded DynamoDB uses AWS's current v2 archive; freeze its tested version/hash for long-term reproducibility. Dependencies are directly pinned, not fully transitively locked.

The old Dockerfile and Compose configuration remain optional legacy examples; the default GitHub and Jenkins pipelines now use Windows native deployment.

## Official documentation

- [AWS DynamoDB Local Java setup](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html)
- [Prometheus native installation](https://prometheus.io/docs/introduction/first_steps/)
- [Jenkins installation](https://www.jenkins.io/doc/book/installing/)
- [Jira/GitHub linking](https://support.atlassian.com/jira-cloud-administration/docs/use-the-github-for-jira-app/)
