# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Set Up Ollama

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai for installation instructions

# Pull a model (llama2 is recommended for starters)
ollama pull llama2

# Or use other models:
# ollama pull mistral
# ollama pull codellama
# ollama pull llama2:13b  # for better quality
```

### Step 2: Set Up Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env if needed (defaults work for local Ollama):
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - OLLAMA_MODEL (default: llama2)
# - PLAID_CLIENT_ID (optional, for bank integration)
# - PLAID_SECRET (optional, for bank integration)
```

### Step 3: Start with Docker

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Step 4: Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

### Step 5: Create Your First Account

1. Navigate to http://localhost:3001
2. Click "Sign up"
3. Register with your email and password
4. Login to access the dashboard

### Step 6: Explore Features

- **Dashboard**: View your financial overview
- **Budgets**: Create and track budgets
- **Goals**: Set financial goals
- **Agents**: Get AI-powered recommendations
  - Financial Planner: `/api/v1/agents/financial-planner`
  - Risk Assessment: `/api/v1/agents/risk-assessment`
  - Learning & Motivation: `/api/v1/agents/learning-motivation`

## 🎯 Next Steps

1. **Try Different Ollama Models**:
   ```bash
   # List available models
   ollama list
   
   # Pull a different model
   ollama pull mistral
   ollama pull codellama
   
   # Update OLLAMA_MODEL in .env
   ```

2. **Train Models** (optional):
   ```bash
   docker-compose exec backend python models/train_forecaster.py
   docker-compose exec backend python models/train_risk_model.py
   ```

3. **Connect Bank Account** (optional):
   - Set up Plaid credentials in `.env`
   - Use Plaid Link to connect accounts

4. **Customize**:
   - Adjust agent prompts in `backend/app/services/agent_service.py`
   - Modify UI components in `frontend/src/components/`
   - Change Ollama model in `.env`

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

### Database connection issues
```bash
# Check database is running
docker-compose ps postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Frontend not connecting to backend
- Check `REACT_APP_API_URL` in frontend
- Verify CORS settings in backend `.env`
- Check backend is running: `curl http://localhost:8001/health`

## 📚 Learn More

- [README.md](README.md) - Full documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- API Docs: http://localhost:8001/docs

## 💡 Tips

- Use Docker logs for debugging: `docker-compose logs -f [service]`
- Test API endpoints with Swagger UI: http://localhost:8001/docs
- Enable hot reload in development (already configured)
- Check health endpoint: `curl http://localhost:8001/health`

