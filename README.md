![CI Pipeline](https://github.com/codewroteit/CI-CD-pipeline/actions/workflows/ci.yml/badge.svg)

# TaskManagement CI/CD Pipeline

An automated pipeline that takes code from a push to a running application with no manual steps. It tests the code, builds a Docker image, deploys to Kubernetes, checks the app's health, and rolls back automatically if the check fails.

## Pipeline flow

push to main → test → build image → deploy v1 → deploy v2 → health check fails → automatic rollback to v1

| Stage | What it does |
|---|---|
| Test | Runs the pytest suite. If a test fails, the deploy job never runs. |
| Publish | Builds the Docker image and pushes it to GitHub Container Registry, tagged with the commit SHA and `latest`. |
| Deploy v1 | Starts a temporary kind (Kubernetes in Docker) cluster, pulls the published image instead of building one, and applies the manifests in `k8s/`. |
| Deploy v2 | Deploys a deliberately broken version whose readiness probe points at a non-existent path. |
| Rollback | When the v2 rollout exceeds its deadline, `kubectl rollout undo` restores v1. |
| Verify | Prints the running image and pods, confirming v1 is serving. |

## How rollback works

- The deployment uses a rolling update with `maxUnavailable: 0`, so the old pods keep serving while the new ones start.
- Each pod has a readiness probe on `/health`.
- If new pods never become ready, `kubectl rollout status` fails after the progress deadline.
- That failure triggers `kubectl rollout undo`, which returns the deployment to the previous revision.

## The app

A small FastAPI service with three endpoints:

- `GET /` returns a status message
- `GET /health` returns `{"status": "healthy"}`
- `GET /version` returns `{"version": "1.0.0"}`

## Repository layout

    .github/workflows/ci.yml   pipeline definition
    app/                       FastAPI application
    test/                      pytest tests
    k8s/                       Kubernetes deployment and service
    Dockerfile                 container image

## Run locally

    pip install fastapi pytest httpx uvicorn
    python -m pytest
    docker build -t taskmanagement-app:local .
    docker run -d -p 8000:8000 --name apptest taskmanagement-app:local
    curl localhost:8000/health

## Limitations

- The kind cluster exists only for the length of one workflow run. The rollback is therefore a same-run demonstration (deploy v1, deploy broken v2, roll back), not a persistent environment.
