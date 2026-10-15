# Serving an ML Model on Kubernetes with KServe

A small, working example of taking a scikit-learn model (`model/model.pkl`) from a file on disk to an HTTP inference endpoint on Kubernetes. The same Flask container is deployed two ways: as a plain Kubernetes `Deployment` + `Service`, and as a KServe `InferenceService`.

## How it works

```
model/model.pkl ──► Flask app (app.py) ──► Docker image ──┬─► Deployment + LoadBalancer Service
                                                           └─► KServe InferenceService
```

`job.yaml` shows a third pattern: a one-off Job that copies the model out of an image into a PersistentVolumeClaim, so a model can be staged in storage separately from the serving image.

## Repository layout

| File | Purpose |
|------|---------|
| `app.py` | Flask server that loads `model/model.pkl` with joblib and exposes `/health` and `/predict` on port 8080 |
| `model/model.pkl` | The trained scikit-learn model |
| `Dockerfile` | Builds the serving image (`python:3.9-slim`, Flask, scikit-learn, joblib, numpy) |
| `deployment.yaml` | Plain Kubernetes `Deployment` (1 replica) and `LoadBalancer` `Service` (80 → 8080) |
| `inference.yaml` | KServe `InferenceService` running the same container |
| `job.yaml` | `PersistentVolumeClaim` (5Gi) and a Job that copies the model into it |

All three workloads request 500m CPU / 1Gi memory and are limited to 1 CPU / 2Gi.

## API

### `GET /health`
```json
{"status": "healthy", "model_loaded": true}
```

### `POST /predict`
Send either `text` (a string or list of strings) or `features` (a flat list of numbers).

```bash
curl -X POST http://<host>/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "this product is great"}'

curl -X POST http://<host>/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
```

Response: `{"prediction": [...]}`. A missing body or missing `text`/`features` returns `400`; a model that failed to load returns `500`.

## Run locally

```bash
pip install flask==3.1.1 scikit-learn==1.7.0 joblib==1.5.1 numpy==2.2.6
python app.py            # http://localhost:8080
```

## Build and push the image

```bash
docker build -t <your-dockerhub-user>/predictor-model:2.4 .
docker push <your-dockerhub-user>/predictor-model:2.4
```

## Deploy

**Prerequisite:** a Kubernetes cluster. KServe (with Knative and Istio) is only needed for the `InferenceService` option.

Plain Kubernetes:
```bash
kubectl apply -f deployment.yaml
kubectl get svc predictor-model-service      # wait for EXTERNAL-IP
```

KServe:
```bash
kubectl apply -f inference.yaml
kubectl get inferenceservice predictor-model
```

Stage the model into a PVC (optional):
```bash
kubectl apply -f job.yaml
kubectl logs job/predictor-model-copy-job
```

## Notes

- The image runs under gunicorn; set `FLASK_DEBUG=1` only when running `python app.py` locally.
- Dependencies are pinned. `scikit-learn==1.7.0` matches the version that produced `model.pkl`; keep them in sync if you retrain.
- All manifests reference `axololtos/predictor-model:2.4`. Build and push that tag (see above) before deploying.
- `inference.yaml` uses a custom container, so it does not use KServe's v1/v2 inference protocol.
- The `job.yaml` PVC is not mounted by the serving workloads yet.

## Author

Built by [axololtos](https://github.com/axololtos).
