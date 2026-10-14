# Teacher demonstration: approximately 8 minutes

## Objective

Explain how a small application change moves from requirement to tested, repeatable deployment. The application is intentionally basic so the DevOps process is easy to see.

## Presentation sequence

1. **Problem and architecture (1 minute):** students need a task tracker. Explain the API, DynamoDB and the delivery diagram in the README.
2. **Plan and traceability (1 minute):** open a real Jira ticket, then its linked GitHub branch and pull request.
3. **Continuous integration (1 minute):** show a GitHub Actions run. Explain input validation tests and the separate deployed CRUD check. Moto tests emulate AWS; the integration check uses DynamoDB Local.
4. **Continuous deployment (2 minutes):** show Jenkins checking out main, testing, rebuilding containers and verifying CRUD. Use a prepared successful run if build time exceeds your slot.
5. **Working application (1 minute):** create a task, list it, mark it complete, and show it still exists after `docker compose restart api`. Use the correct Compose project (`-p taskflow-demo` for Jenkins).
6. **Failure and recovery (1 minute):** show a saved genuine failing test run followed by its fix. Explain that failed tests prevent deployment. Do not break the live demo just before presenting.
7. **Limitations and learning (1 minute):** explain local versus AWS DynamoDB, secret handling, persistent data, and why production would need authentication and a stronger rollout/rollback strategy.

For the required monitoring stage, add two minutes to show Prometheus target health, response/error metrics and a saved or live service-down alert followed by recovery. Follow `monitoring.md`. Use the title **End-to-end DevOps pipeline for a DynamoDB task tracker**.

## Evidence checklist

- [ ] Teacher confirms required tools, cloud requirements and deliverable format.
- [ ] README includes architecture and reproducible commands.
- [ ] Jira ticket has acceptance criteria and actual development links.
- [ ] GitHub repository has meaningful commits and a reviewed PR if a reviewer is available.
- [ ] GitHub Actions run is green, including container integration testing.
- [ ] Jenkins stages and JUnit test results are visible.
- [ ] Running API creates, lists, updates and deletes a task.
- [ ] A task survives an API restart.
- [ ] Prometheus target, traffic/latency graphs and an outage/recovery alert are demonstrated.
- [ ] Real failure and successful recovery evidence is saved.
- [ ] If AWS is required, show the real table and item in the AWS console.

## Short viva answers

**Why DynamoDB?** It stores flexible task documents by a unique key and integrates with AWS. This example is too small to claim a performance advantage over other databases.

**Why both GitHub Actions and Jenkins?** Actions validates proposed changes near the PR. Jenkins demonstrates deployment from main to a controlled demo environment. Using both is educational; a real small team may choose one.

**What is CI/CD?** CI automatically checks integrated changes. This Jenkins pipeline demonstrates continuous deployment to a local demo after tests pass.

**What does Jira add?** It connects a requirement and acceptance criteria to the branch, commit and PR that implement it.

**What did you automate?** Tests, image builds, table initialization, deployment and deployed CRUD verification. Jira transitions and the initial account setup remain manual.

Acceptance cannot be guaranteed without the teacher's rubric. Match the evidence above to each rubric item before submission.
