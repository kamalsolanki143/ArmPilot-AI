# AWS Graviton Deployment

Deploy ArmPilot-AI on AWS Graviton (Arm64) instances for production workloads.

## Why Graviton

- **Price/Performance** — 40% better price-performance vs comparable x86 instances
- **Native Arm64** — No emulation; llama.cpp runs natively with NEON/SVE2
- **Memory Bandwidth** — High bandwidth for LLM inference workloads
- **Scale** — Horizontal scaling behind Application Load Balancer

## Architecture

```
                        ┌─────────────┐
                        │     ALB     │
                        │  (HTTPS)    │
                        └──────┬──────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
         ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
         │  Graviton  │  │  Graviton  │  │  Graviton  │
         │  c7g.xl    │  │  c7g.xl    │  │  c7g.xl    │
         │ Backend    │  │ Backend    │  │ Backend    │
         └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                        ┌──────▼──────┐
                        │  EFS / S3   │
                        │Model Storage│
                        └─────────────┘
```

## Instance Selection

| Instance | vCPU | Memory | Network | Use Case |
|----------|------|--------|---------|----------|
| c7g.medium | 2 | 4 GB | Up to 12.5 Gbps | Dev/test |
| c7g.large | 4 | 8 GB | Up to 12.5 Gbps | Small models (1-3B) |
| c7g.xlarge | 8 | 16 GB | Up to 12.5 Gbps | Medium models (3-7B) |
| c7g.2xlarge | 16 | 32 GB | Up to 12.5 Gbps | Large models (7-13B) |
| c7g.4xlarge | 32 | 64 GB | Up to 12.5 Gbps | Very large models |
| c7gn.xlarge | 8 | 16 GB | Up to 25 Gbps | Network-intensive |

## Setup Steps

### 1. Launch Instance

```bash
# Using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type c7g.2xlarge \
  --architecture arm64 \
  --key-name my-key \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx \
  --block-device-mappings '[{
    "DeviceName": "/dev/sda1",
    "Ebs": {
      "VolumeSize": 100,
      "VolumeType": "gp3",
      "Iops": 3000,
      "Throughput": 125
    }
  }]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=armpilot-prod}]'
```

### 2. Connect and Install

```bash
ssh -i my-key.pem ubuntu@<instance-ip>

# System updates
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Clone and setup
git clone https://github.com/krrishyaduka/ArmPilot-AI.git
cd ArmPilot-AI
bash scripts/setup.sh
```

### 3. Transfer Models

```bash
# From local machine
scp -i my-key.pem models/*.gguf ubuntu@<instance-ip>:~/ArmPilot-AI/models/

# Or download directly
wget -P models/ https://huggingface.co/TheBloke/...
```

### 4. Configure for Production

```bash
cp .env.example .env
vim .env
```

```bash
ARMPILOT_HOST=0.0.0.0
ARMPILOT_PORT=8000
ARMPILOT_DEBUG=false
ARMPILOT_LOG_LEVEL=WARNING
ARMPILOT_DEFAULT_THREADS=8
ARMPILOT_JWT_SECRET_KEY=<generate-strong-key>
```

### 5. Create Systemd Service

```bash
sudo tee /etc/systemd/system/armpilot.service << 'EOF'
[Unit]
Description=ArmPilot-AI API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ArmPilot-AI/backend
ExecStart=/home/ubuntu/ArmPilot-AI/backend/.venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable armpilot
sudo systemctl start armpilot
```

### 6. Configure Nginx (Optional)

```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/armpilot << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/armpilot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 7. SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Auto-Scaling

### ECS with Fargate

```json
{
  "family": "armpilot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "8192",
  "containerDefinitions": [{
    "name": "armpilot",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/armpilot:latest",
    "portMappings": [{"containerPort": 8000}],
    "environment": [
      {"name": "ARMPILOT_DEBUG", "value": "false"}
    ],
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
      "interval": 30,
      "timeout": 5
    }
  }]
}
```

### ALB Target Group

- Health check path: `/health`
- Health check interval: 30 seconds
- Healthy threshold: 2
- Unhealthy threshold: 3

## Cost Optimization

| Strategy | Savings |
|----------|---------|
| Reserved Instances (1yr) | ~30% |
| Savings Plans (1yr) | ~20% |
| Spot Instances | ~60% |
| Right-sizing with Graviton | ~40% vs x86 |

## Monitoring

```bash
# CloudWatch agent for custom metrics
aws cloudwatch put-metric-data \
  --namespace ArmPilot \
  --metric-data MetricName=TokensPerSecond,Value=34.7,Unit=Count/Second
```

## Security Group Rules

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH access |
| 80 | TCP | 0.0.0.0/0 | HTTP (redirect to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 8000 | TCP | VPC CIDR | API (internal only) |
