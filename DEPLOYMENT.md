# RESQ2FHIR - Deployment Checklist & Production Guide

## Pre-Deployment Checklist

### 1. Code Quality
- [ ] All Python files follow PEP 8
- [ ] Type hints added to functions
- [ ] Docstrings for public methods
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Tests pass: `python test_converter.py`
- [ ] Structure verified: `python verify_structure.py`

### 2. Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `CONVERTER_CMD` environment variable set
- [ ] Database connections tested
- [ ] VALIDATOR_BASE_URL verified
- [ ] HAPI_BASE_URL configured (if needed)
- [ ] WORKDIR path writable

### 3. Data
- [ ] Input CSV validated
- [ ] CSV encoding UTF-8 confirmed
- [ ] All required columns present
- [ ] Sample data transformation tested
- [ ] Output bundles inspected for correctness

### 4. Dependencies
- [ ] All packages in `requirements.txt`
- [ ] Version numbers pinned
- [ ] No security vulnerabilities: `pip audit`
- [ ] Compatibility checked: `python --version >= 3.9`

### 5. Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] API endpoints tested with curl
- [ ] FHIR validation passed
- [ ] Large dataset tested (if applicable)

### 6. Documentation
- [ ] README.md reviewed
- [ ] SETUP.md accurate
- [ ] API documentation complete
- [ ] Error messages helpful
- [ ] Examples working

### 7. Security
- [ ] No secrets in code
- [ ] `.env` in `.gitignore`
- [ ] HTTPS enabled in production
- [ ] Input validation implemented
- [ ] Rate limiting considered
- [ ] Access logs configured

### 8. Monitoring
- [ ] Logging configured
- [ ] Error alerts setup
- [ ] Job monitoring available
- [ ] Disk space monitoring
- [ ] API response time tracking

## Local Development Deployment

```bash
# 1. Install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env

# 3. Test
python setup_demo.py
python test_converter.py --verbose

# 4. Run converter
python scripts/transform.py --input data/data-extended.csv --outdir ./bundles --verbose

# 5. Run API
uvicorn scripts.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Deployment

### Build Image
```bash
docker build -t resq2fhir:latest .

# With build args
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t resq2fhir:1.0.0 .
```

### Run Container
```bash
docker run \
  -p 8000:8000 \
  -e CONVERTER_CMD="python scripts/transform.py --input {in} --outdir {out}" \
  -e VALIDATOR_BASE_URL="http://validator:8085" \
  -v /data:/app/data \
  -v /workdir:/app/workdir \
  resq2fhir:latest
```

### With Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Clean up
docker-compose down -v
```

## Production Deployment Options

### 1. Kubernetes Deployment

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resq2fhir-api
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resq2fhir
  template:
    metadata:
      labels:
        app: resq2fhir
    spec:
      containers:
      - name: api
        image: resq2fhir:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: CONVERTER_CMD
          valueFrom:
            configMapKeyRef:
              name: resq2fhir-config
              key: converter-cmd
        - name: VALIDATOR_BASE_URL
          value: "http://validator-service:8085"
        - name: HAPI_BASE_URL
          value: "http://hapi-service:8080/fhir"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        volumeMounts:
        - name: workdir
          mountPath: /app/workdir
      volumes:
      - name: workdir
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: resq2fhir-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: resq2fhir
```

Deploy:
```bash
kubectl apply -f k8s/
kubectl get pods -l app=resq2fhir
kubectl logs -f deployment/resq2fhir-api
```

### 2. AWS ECS Deployment

Create `ecs-task-definition.json`:
```json
{
  "family": "resq2fhir",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "resq2fhir-api",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/resq2fhir:latest",
      "portMappings": [
        {
          "containerPort": 8000
        }
      ],
      "environment": [
        {
          "name": "CONVERTER_CMD",
          "value": "python scripts/transform.py --input {in} --outdir {out}"
        }
      ],
      "secrets": [
        {
          "name": "HAPI_BEARER",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:hapi-bearer"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/resq2fhir",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Deploy:
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
aws ecs create-service --cluster default --service-name resq2fhir --task-definition resq2fhir --desired-count 2
```

### 3. Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name resq2fhir \
  --image resq2fhir:latest \
  --cpu 1 --memory 1.5 \
  --ports 8000 \
  --environment-variables CONVERTER_CMD="python scripts/transform.py --input {in} --outdir {out}" \
  --ip-address Public \
  --dns-name-label resq2fhir
```

### 4. Traditional VM/Server

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install python3.11 python3-pip

# 2. Clone repo
git clone <repo> /opt/resq2fhir
cd /opt/resq2fhir

# 3. Setup venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
nano .env  # Edit with production values

# 5. Setup systemd service
sudo tee /etc/systemd/system/resq2fhir.service > /dev/null <<EOF
[Unit]
Description=RESQ2FHIR API
After=network.target

[Service]
Type=notify
User=resq2fhir
WorkingDirectory=/opt/resq2fhir
Environment="PATH=/opt/resq2fhir/venv/bin"
ExecStart=/opt/resq2fhir/venv/bin/uvicorn scripts.main:app --host 0.0.0.0 --port 8000
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 6. Start service
sudo systemctl daemon-reload
sudo systemctl enable resq2fhir
sudo systemctl start resq2fhir
sudo journalctl -u resq2fhir -f
```

## Post-Deployment Validation

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Test Conversion
```bash
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@test_data.csv"
```

### 3. Check Logs
```bash
# Docker
docker logs -f resq2fhir-api

# Kubernetes
kubectl logs -f pod/resq2fhir-api-xxx

# Systemd
journalctl -u resq2fhir -f
```

### 4. Validate Bundles
```bash
curl -X POST http://validator:8085/api/validate/bundle \
  -H "Content-Type: application/json" \
  -d @output_bundle.json
```

## Performance Tuning

### API Server
```bash
# Production gunicorn + uvicorn
gunicorn scripts.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

### Memory Optimization
- For large CSV: Use chunked processing
- For many jobs: Implement cleanup
- Monitor: `free -h`, `du -sh ./workdir`

### CPU Optimization
- Increase `parallelism` for validation
- Use multiprocessing for CSV parsing
- Profile with `cProfile`

## Backup & Recovery

### Data Backup
```bash
# Backup generated bundles
tar -czf backup-bundles-$(date +%Y%m%d).tar.gz workdir/jobs/

# Backup configuration
tar -czf backup-config-$(date +%Y%m%d).tar.gz .env

# Send to S3
aws s3 cp backup-bundles-*.tar.gz s3://my-bucket/backups/
```

### Database Recovery (if using HAPI)
```bash
# HAPI FHIR backup
docker exec hapi-container bash -c "mysqldump -u root -p hapi > backup.sql"
```

## Monitoring & Alerting

### Prometheus Metrics
Add to uvicorn:
```bash
pip install prometheus-client
```

```python
from prometheus_client import Counter, Histogram, start_http_server

requests_total = Counter('resq2fhir_requests_total', 'Total requests')
request_duration = Histogram('resq2fhir_request_duration_seconds', 'Request duration')
```

### Health Checks
```bash
# Configure health check in load balancer
GET /health → 200 OK
```

### Log Aggregation
```bash
# ELK Stack, Splunk, CloudWatch, etc.
# Configure in docker-compose or Kubernetes
```

## Rollback Plan

If deployment fails:

```bash
# Docker
docker pull resq2fhir:previous
docker tag resq2fhir:previous resq2fhir:latest
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/resq2fhir-api

# Git
git revert HEAD
```

## Documentation
- [ ] Update deployment docs
- [ ] Record deployment date
- [ ] Document any customizations
- [ ] Update runbooks for ops team
- [ ] Create incident response plan

## Sign-off
- [ ] Development team approval
- [ ] QA sign-off
- [ ] Security review passed
- [ ] Operations team trained
- [ ] Ready for production

---

**Deployment Date:** ________________  
**Deployed By:** ________________  
**Environment:** [ ] Development [ ] Staging [ ] Production  
**Version:** ________________  
**Notes:** ________________________________________________

---

For issues during deployment, refer to:
- README.md
- SETUP.md
- Docker logs
- Kubernetes/ECS logs
