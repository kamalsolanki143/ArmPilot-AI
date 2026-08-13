# Production Deployment

Guide for deploying ArmPilot-AI in production environments.

## Production Checklist

### Security

- [ ] Generate a strong JWT secret: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- [ ] Set `ARMPILOT_DEBUG=false`
- [ ] Set `ARMPILOT_LOG_LEVEL=WARNING`
- [ ] Configure CORS for your domain only
- [ ] Enable rate limiting
- [ ] Set up SSL/TLS termination
- [ ] Restrict API access (enable authentication)
- [ ] Run behind a reverse proxy (Nginx/Traefik)

### Performance

- [ ] Use production hardware profile (Neoverse N1/V2)
- [ ] Set thread count to physical core count
- [ ] Use batch size 8-64 depending on workload
- [ ] Enable quantized KV cache (Q8_0)
- [ ] Place model files on fast storage (NVMe/EFS)
- [ ] Set context length appropriately (2048-4096)

### Reliability

- [ ] Configure health check endpoint
- [ ] Set up log rotation
- [ ] Enable rate limiting (60 req/min)
- [ ] Configure automatic restarts
- [ ] Set up monitoring and alerting
- [ ] Test backup and recovery

### Storage

- [ ] Models on persistent storage (EFS, EBS, or local NVMe)
- [ ] Back up reports and optimization results
- [ ] Configure log retention (30 days)

## Environment Configuration

### Production `.env`

```bash
# Server
ARMPILOT_HOST=0.0.0.0
ARMPILOT_PORT=8000
ARMPILOT_DEBUG=false
ARMPILOT_LOG_LEVEL=WARNING

# Security
ARMPILOT_JWT_SECRET_KEY=<64-byte-random-secret>
ARMPILOT_CORS_ORIGINS=["https://app.yourdomain.com"]

# Inference
ARMPILOT_DEFAULT_RUNTIME=llama.cpp
ARMPILOT_DEFAULT_THREADS=8
ARMPILOT_DEFAULT_BATCH_SIZE=512
ARMPILOT_DEFAULT_CONTEXT_LENGTH=2048

# Benchmark
ARMPILOT_BENCHMARK_DURATION_DEFAULT=120
ARMPILOT_BENCHMARK_CONCURRENCY_DEFAULT=4
ARMPILOT_BENCHMARK_WARMUP_REQUESTS=5

# Optimization
ARMPILOT_OPTIMIZATION_MAX_CANDIDATES=8
ARMPILOT_OPTIMIZATION_BENCHMARK_PER_CANDIDATE=10
```

## Reverse Proxy Configuration

### Nginx

```nginx
upstream armpilot {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # API endpoints
    location /v1/ {
        proxy_pass http://armpilot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /api/ {
        proxy_pass http://armpilot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;  # Long timeout for benchmarks
    }

    location /auth/ {
        proxy_pass http://armpilot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://armpilot;
    }

    location /docs {
        proxy_pass http://armpilot;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    location /v1/chat/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://armpilot;
    }
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

## Monitoring

### Health Check

```bash
# Automated health check
curl -sf http://localhost:8000/health || alert "ArmPilot is down"
```

### Key Metrics to Monitor

| Metric | Warning | Critical |
|--------|---------|----------|
| API response time | >500ms | >2s |
| CPU usage | >80% | >95% |
| Memory usage | >70% | >90% |
| TTFT | >200ms | >500ms |
| Tokens/sec | <10 | <5 |
| Error rate | >1% | >5% |

### Log Aggregation

```bash
# Log rotation (add to crontab)
0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/armpilot
```

```ini
# /etc/logrotate.d/armpilot
/var/log/armpilot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

## Backup Strategy

| What | Frequency | Retention |
|------|-----------|-----------|
| Model files | On change | Permanent |
| Benchmark results | Daily | 90 days |
| Optimization results | On completion | 90 days |
| Reports | On generation | 90 days |
| Database (SQLite) | Daily | 30 days |
| Logs | Daily | 30 days |

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y-%m-%d)
tar -czf "backup-$DATE.tar.gz" \
  models/ data/ reports/ logs/ \
  --exclude='models/*.tmp'
aws s3 cp "backup-$DATE.tar.gz" s3://your-backup-bucket/armpilot/
```

## Scaling

### Vertical Scaling

Increase instance size to handle larger models or higher concurrency:

| Model Size | Minimum RAM | Recommended Instance |
|-----------|-------------|---------------------|
| 1-3B | 4 GB | c7g.large |
| 3-7B | 8 GB | c7g.xlarge |
| 7-13B | 16 GB | c7g.2xlarge |
| 13-30B | 32 GB | c7g.4xlarge |

### Horizontal Scaling

Run multiple backend instances behind a load balancer:

```bash
# Docker Compose scale
docker compose -f docker-compose.prod.yml up -d --scale backend=3
```

Each instance can handle one model at a time. Use a shared model store (EFS) for consistency.

## Rollback

```bash
# Quick rollback
git checkout v0.1.0
bash scripts/run_server.sh

# Docker rollback
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```
