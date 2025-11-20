# Elastic Stack Sandbox

Compact observability lab: a Flask orders API emits structured JSON logs, Filebeat autodiscovers the container, Logstash normalizes fields, and Elasticsearch/Kibana surface the data. The repo stays small while demonstrating logging, alerting, and CI/CD end to end.

## Stack
- `service/`: Flask API exposing `/orders`, `/chaos`, and `/health`; logs structured JSON to stdout.
- `deploy/docker-compose.yml`: one-command lab with Elasticsearch, Kibana, Logstash, Filebeat, and the API container.
- `scripts/error_alert.py`: log-based alert that counts `ERROR` events and posts to a webhook.
- `.github/workflows/ci.yml`: GitHub Actions pipeline running tests, building/pushing the image, deploying via SSH, then running the alert hook.

## Quickstart
```bash
# Build the image and start the stack
docker compose -f deploy/docker-compose.yml up --build -d

# Send orders and generate noisy traffic
curl -X POST http://localhost:8080/orders -H 'content-type: application/json' \
  -d '{"customer":"demo","total":15}'
watch -n1 curl -s http://localhost:8080/chaos

# Open Kibana
open http://localhost:5601
```
> Filebeat needs access to `/var/lib/docker/containers` and `/var/run/docker.sock`. Run Compose as root or adjust permissions accordingly.

After generating traffic, the `orders-*` index should appear in Kibana Discover with parsed fields such as `event.customer` and `event.latency_ms`.

## Data Flow
```
orders-api (Flask) -> Filebeat autodiscover -> Logstash pipeline -> Elasticsearch index -> Kibana dashboards
                                                        -> stdout (debug)
```
- `service/app.py` logs JSON so every field survives ingestion.
- Filebeat watches containers with the label `co.elastic.logs/module=orders`, making it easy to add more services.
- Elasticsearch runs without security for simplicity; add users or API keys before exposing it.

## CI/CD
Workflow stages:
1. **test** — install `requirements-dev.txt` and run pytest.
2. **build** — authenticate to GHCR and push `orders-api`.
3. **deploy** — SSH to a remote host, update the Compose stack, then run the alert script with production credentials.

Required secrets:
- `GHCR_TOKEN`
- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY`
- `ELASTICSEARCH_URL`, `ALERT_WEBHOOK`

## Alert Script
`scripts/error_alert.py` runs an `_count` query against `orders-*` for the last `WINDOW_MINUTES` (default 5). If `ALERT_THRESHOLD` is reached, it POSTs a short message to `ALERT_WEBHOOK`.

```bash
ELASTICSEARCH_URL=http://localhost:9200 \
ALERT_THRESHOLD=1 \
python scripts/error_alert.py
```

## Extend It
- Enable Elastic security and switch Beats/Logstash to API keys.
- Replace docker-compose with Terraform + Ansible or Nomad/Kubernetes manifests.
- Build Kibana dashboards, export NDJSON, and commit them under `docs/`.
- Extend Actions with linting, trivy scans, or canary deploy stages.
