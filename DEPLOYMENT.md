# Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Python 3.10+ (for local development)
- Node.js 18+ (for local development)

## Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update `.env` with your configuration:
   - Set `SECRET_KEY` to a strong random string
   - Configure `DATABASE_URL` if not using Docker
   - Add your Plaid API credentials
   - Add your OpenAI API key
   - Configure CORS origins

## Docker Deployment

### Quick Start

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Services

```bash
# Start only database
docker-compose up -d postgres redis

# Start backend
docker-compose up -d backend

# Start frontend
docker-compose up -d frontend
```

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (if using Alembic)
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Training Models

```bash
# Train time series forecaster
cd models
python train_forecaster.py

# Train risk assessment model
python train_risk_model.py
```

## Production Deployment

### Docker Production

1. Update `docker-compose.yml` with production settings
2. Use production Docker images
3. Configure environment variables
4. Set up SSL/TLS certificates
5. Configure reverse proxy (nginx)

### Cloud Deployment

#### AWS
- Use ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- CloudFront for CDN

#### Google Cloud
- Cloud Run for containers
- Cloud SQL for PostgreSQL
- Cloud Memorystore for Redis

#### Azure
- Container Instances or AKS
- Azure Database for PostgreSQL
- Azure Cache for Redis

## Monitoring

- Health checks: `http://localhost:8001/health`
- API docs: `http://localhost:8001/docs`
- Logs: Configure logging level in `.env`

## Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable authentication
- [ ] Regular security updates
- [ ] Backup database regularly

## Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Check network connectivity

### API Errors
- Check logs: `docker-compose logs backend`
- Verify environment variables
- Check API key configurations

### Frontend Issues
- Check API URL in `.env`
- Verify CORS settings
- Check browser console for errors

