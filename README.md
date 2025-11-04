# Personal Finance AI Platform

A production-grade multi-agent AI platform for personalized financial planning, budgeting, and investment advice.

## 🚀 Features

- **Multi-Agent System**: LangGraph orchestration with 4 specialized agents
  - Financial Planner Agent: Personalized budget recommendations
  - Risk Assessment Agent: Investment risk analysis using PyTorch models
  - Learning & Motivation Agent: Motivational content and tips
  - Notification & Alert Agent: Budget alerts and bill reminders
- **AI Models**: PyTorch-based time-series forecasting and risk assessment
- **Interactive Frontend**: Anime.js animations for engaging user experience
- **Bank Integration**: Plaid API for real-time transaction data
- **Containerized**: Docker-based microservices architecture
- **Production Ready**: Comprehensive logging, error handling, security, and testing

## 🎥 Video Demo

Watch the demo video: **[Screencast from 2025-11-03 21-55-06.webm](assets/Screencast%20from%202025-11-03%2021-55-06.webm)**

> **Note:** GitHub doesn't support inline video playback. Click the link above to download or view the video in your browser.

## 📁 Architecture

```
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes and endpoints
│   │   ├── core/        # Configuration, security, logging
│   │   ├── db/          # Database models and connection
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic services
│   └── tests/           # Test suite
├── agents/              # LangGraph multi-agent orchestrator
├── models/              # PyTorch ML models and training scripts
├── frontend/            # React frontend with Anime.js
│   ├── src/
│   │   ├── components/  # React components
│   │   └── context/     # React context providers
├── docker/              # Docker configurations
└── docs/                # Documentation
```

## 🏃 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for local development)

### Running with Docker

```bash
# Clone or navigate to project directory
cd PersonalFInance

# Install and set up Ollama (required for agents)
# Visit https://ollama.ai for installation instructions
ollama pull llama2

# Copy environment file
cp .env.example .env
# Edit .env if needed (defaults work for local Ollama)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3001
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📚 API Documentation

Once running, access interactive API documentation:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## 🔧 Configuration

### Environment Variables

See `.env.example` for required environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key (change in production!)
- `PLAID_CLIENT_ID`: Plaid API client ID
- `PLAID_SECRET`: Plaid API secret
- `PLAID_ENV`: Plaid environment (sandbox/development/production)
- `OLLAMA_BASE_URL`: Ollama API URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: llama2)
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins

## 🤖 Multi-Agent System

The platform uses LangGraph to orchestrate multiple AI agents:

1. **Financial Planner Agent**: Analyzes user financial data and provides budget recommendations
2. **Risk Assessment Agent**: Uses PyTorch models to assess investment risk
3. **Learning & Motivation Agent**: Provides motivational quotes and financial tips
4. **Notification & Alert Agent**: Monitors budgets and generates alerts

## 🧠 AI Models

### Time Series Forecasting
- LSTM-based model for income/expense prediction
- Train with: `python models/train_forecaster.py`

### Risk Assessment
- Neural network for financial risk evaluation
- Train with: `python models/train_risk_model.py`

## 🎨 Frontend Features

- **Animated Dashboard**: Real-time financial overview with Anime.js animations
- **Budget Progress Bars**: Animated progress tracking
- **Goal Visualization**: Circular progress indicators
- **Interactive Charts**: Financial trends visualization
- **Motivational Widget**: Dynamic quotes and tips

## 🧪 Testing

```bash
cd backend
pytest
```

## 📦 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection protection (SQLAlchemy ORM)

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

## 📧 Support

For issues and questions, please open an issue on GitHub.

