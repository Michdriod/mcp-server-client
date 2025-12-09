# Database Query Assistant - Deployment Guide

Complete production deployment guide for Docker, Kubernetes, and cloud providers.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Docker Deployment](#docker-deployment)
4. [Production Checklist](#production-checklist)
5. [Monitoring & Observability](#monitoring--observability)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                Load Balancer (NGINX)                │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐
│   Web UI     │ │ MCP Server│ │   Celery   │
│ (Frontend)   │ │(FastMCP)  │ │   Worker   │
└───────┬──────┘ └───┬───────┘ └─────┬──────┘
        │            │               │
        └────────────┼───────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
   │PostgreSQL│ │ Redis  │  │ Celery │
   │  (DB)    │ │(Cache) │  │  Beat  │
   └──────────┘ └────────┘  └────────┘
```

### Components

- **Web UI**: External frontend (Streamlit removed)
- **MCP Server**: FastMCP with 17 tools
- **Celery Worker**: Background job processing
- **Celery Beat**: Task scheduler
- **PostgreSQL**: Primary database
- **Redis**: Cache + message broker
- **NGINX**: Load balancer & reverse proxy

---

## Prerequisites

### System Requirements

**Minimum:**
- 4 CPU cores
- 8 GB RAM
- 50 GB storage
- PostgreSQL 14+
- Redis 6+

**Recommended:**
- 8+ CPU cores
- 16+ GB RAM
- 100+ GB SSD
- High-performance network

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+ (for Docker deployment)
- Kubernetes 1.25+ (for K8s deployment)
- kubectl configured
- Helm 3.0+ (optional)

### External Services

- Groq API key ([console.groq.com](https://console.groq.com))
- SMTP server (Gmail, SendGrid, etc.)
- TLS certificates (Let's Encrypt recommended)

---

## Docker Deployment

### Quick Start

1. **Clone Repository**

```bash
git clone https://github.com/your-org/mcp-server-client.git
cd mcp-server-client
```

2. **Configure Environment**

```bash
cp .env.example .env
vim .env  # Edit with your values
```

Required variables:
```bash
DB_NAME=dbquery
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=postgres
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

GROQ_API_KEY=your_groq_api_key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@yourcompany.com
```

3. **Build Images**

```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build mcp-server
```

4. **Start Services**

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

5. **Initialize Database**

```bash
# Run migrations
docker-compose exec mcp-server alembic upgrade head

# Or import SQL script
docker-compose exec postgres psql -U postgres dbquery < setup.sql
```

6. **Access Application**

- Web UI: `http://localhost:8501`
- NGINX: `http://localhost` (if enabled)

### Production Docker Deployment

1. **Use External Databases**

Update `docker-compose.yml` to remove postgres and redis services, configure external connections:

```yaml
services:
  mcp-server:
    environment:
      - DB_HOST=your-postgres.example.com
      - REDIS_HOST=your-redis.example.com
```

2. **Configure Persistent Storage**

```yaml
volumes:
  exports:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server.example.com
      device: ":/exports"
```

3. **Set Resource Limits**

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

4. **Configure Health Checks**

Already included in Dockerfile. Monitor:

```bash
docker inspect --format='{{.State.Health.Status}}' container_name
```

5. **Set Up Logging**

```bash
# Configure log driver
docker-compose.yml:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### Docker Scaling

```bash
# Scale specific service
docker-compose up -d --scale celery-worker=5

# Scale multiple services
docker-compose up -d --scale mcp-server=3 --scale celery-worker=10
```

---

## Production Checklist

### Security

- [ ] Strong passwords for all services
- [ ] TLS certificates installed
- [ ] HTTPS enforced
- [ ] Network policies configured
- [ ] RBAC properly set up
- [ ] Secrets management (Vault, AWS Secrets Manager)
- [ ] Security scanning enabled
- [ ] Regular security updates

### High Availability

- [ ] Multi-AZ deployment
- [ ] Database replication configured
- [ ] Redis cluster/replication
- [ ] Load balancer configured
- [ ] Auto-scaling enabled (HPA)
- [ ] Pod disruption budgets set
- [ ] Health checks configured
- [ ] Graceful shutdown implemented

### Monitoring

- [ ] Prometheus metrics enabled
- [ ] Grafana dashboards configured
- [ ] Alert rules set up
- [ ] Log aggregation (ELK/Loki)
- [ ] APM configured (New Relic, Datadog)
- [ ] Uptime monitoring
- [ ] Error tracking (Sentry)

### Backup & Recovery

- [ ] Database backups automated
- [ ] Backup retention policy set
- [ ] Disaster recovery plan documented
- [ ] Recovery tested
- [ ] PVC snapshots configured

### Performance

- [ ] Connection pooling optimized
- [ ] Cache hit rate monitored
- [ ] Query performance analyzed
- [ ] CDN configured (if applicable)
- [ ] Resource limits tuned
- [ ] Database indexes optimized

### Documentation

- [ ] Deployment runbook created
- [ ] Architecture diagram updated
- [ ] API documentation complete
- [ ] Incident response plan ready
- [ ] Contact list maintained

---

## Monitoring & Observability

### Metrics

**Prometheus + Grafana**

1. Install Prometheus Operator:

```bash
kubectl create namespace monitoring
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
```

2. Add ServiceMonitor:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dbquery-metrics
spec:
  selector:
    matchLabels:
      app: mcp-server
  endpoints:
  - port: metrics
    interval: 30s
```

### Logging

**ELK Stack**

```bash
# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch -n logging

# Install Kibana
helm install kibana elastic/kibana -n logging

# Install Filebeat
helm install filebeat elastic/filebeat -n logging
```

### Tracing

**Jaeger**

```bash
kubectl create namespace observability
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml -n observability
```

---

## Troubleshooting

### Common Issues

**1. Pods Not Starting**

```bash
kubectl describe pod <pod-name> -n dbquery
kubectl logs <pod-name> -n dbquery
```

**2. Database Connection Failed**

```bash
# Test connection
kubectl exec -it deployment/mcp-server -n dbquery -- \
  python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://user:pass@host:5432/db'))"
```

**3. Redis Connection Failed**

```bash
# Test connection
kubectl exec -it deployment/mcp-server -n dbquery -- \
  python -c "import redis; r = redis.from_url('redis://:pass@host:6379/0'); print(r.ping())"
```

**4. Out of Memory**

```bash
# Check resource usage
kubectl top pods -n dbquery

# Increase limits
kubectl edit deployment mcp-server -n dbquery
```

**5. High Latency**

- Check database query performance
- Verify cache hit rate
- Review connection pool settings
- Scale up replicas

### Support

For production issues:
1. Check monitoring dashboards
2. Review logs in centralized system
3. Check health endpoints
4. Review resource usage
5. Contact support team

---

## Appendix

### Useful Commands

```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes

# View resources
kubectl get all -n dbquery
kubectl top pods -n dbquery

# Restart deployments
kubectl rollout restart deployment -n dbquery

# Scale deployments
kubectl scale deployment mcp-server --replicas=5 -n dbquery

# Port forwarding
kubectl port-forward svc/web-ui 8501:8501 -n dbquery

# Execute commands
kubectl exec -it deployment/mcp-server -n dbquery -- /bin/sh

# View logs
kubectl logs -f deployment/mcp-server -n dbquery
kubectl logs --tail=100 -l app=celery-worker -n dbquery

# Describe resources
kubectl describe pod <pod-name> -n dbquery
kubectl describe service <service-name> -n dbquery
```

### Performance Tuning

**Database:**
- Connection pool: 20 min, 40 max
- Query timeout: 30s
- Index optimization

**Redis:**
- Max memory: 2GB
- Eviction policy: allkeys-lru
- Connection pool: 50

**Application:**
- Worker concurrency: 4 per pod
- Cache TTL: 5min (queries), 1hr (schema)
- Rate limit: 100 req/user/hour

---

**Last Updated:** Phase 5 & 6 Complete  
**Version:** 1.0.0  
**Maintained by:** Database Query Assistant Team
