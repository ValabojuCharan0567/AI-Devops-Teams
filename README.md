# AI DevOps Team

Multi-agent AI system for automating DevOps incident investigation.

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

1. **Create virtual environment:**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install .
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key or configure local LLM settings
```

4. **Run development server:**

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Interactive Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)

## Project Structure

```
ai-devops-team/
├── app/                    # Main application config
│   ├── __init__.py
│   └── config.py          # Pydantic settings
├── api/                    # API routes and schemas
│   ├── __init__.py
│   ├── routes.py          # API endpoints
│   ├── schemas.py         # Pydantic models
│   └── middleware.py      # Request/response middleware
├── services/              # Business logic
│   ├── __init__.py
│   └── incident_service.py
├── agents/                # LangGraph agent definitions
├── graphs/                # Workflow graphs
├── tools/                 # Agent tools
├── tests/                 # Test suite
├── docs/                  # Documentation
├── main.py               # FastAPI app entry point
├── pyproject.toml        # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## API Endpoints

### Health Check

- `GET /api/health` - Server health status

### Incidents

- `POST /api/incidents` - Create new incident
- `GET /api/incidents` - List all incidents
- `GET /api/incidents/{incident_id}` - Get incident details
- `GET /api/incidents/{incident_id}/report` - Get investigation report

### Example Request

```bash
curl -X POST "http://localhost:8000/api/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High CPU usage in payment service",
    "description": "Payment service pods showing 95% CPU usage for last 10 minutes",
    "environment": "prod",
    "severity": "high",
    "affected_service": "payment-service"
  }'
```

## Development

### Running Tests

```bash
pytest -v --cov=app tests/
```

### Code Quality

```bash
# Format code
black . --exclude=.venv

# Lint
pylint app/ api/ services/ tests/

# Type check
mypy app/ api/ services/
```

## Documentation

See the `docs/` folder for detailed documentation:

- `01-PRD.md` - Product requirements
- `02-SRS.md` - System requirements
- `03-SYSTEM-DESIGN.md` - Architecture design
- `04-LOW-LEVEL-DESIGN.md` - Implementation details
- `05-DATABASE-DESIGN.md` - Database schema
- `06-AGENT-DESIGN.md` - AI agent specifications
- `07-PROJECT-ROADMAP.md` - Project timeline
- `08-TESTING-STRATEGY.md` - Testing approach
- `09-DEPLOYMENT-GUIDE.md` - Deployment instructions

## Technology Stack

- **Framework:** FastAPI 0.138.1
- **ASGI Server:** Uvicorn 0.49.0
- **AI Orchestration:** LangGraph 1.2.6
- **LLM:** LangChain 1.3.11 + OpenAI 2.44.0
- **Validation:** Pydantic 2.13.4
- **Testing:** Pytest 7.4.3
- **Code Quality:** Black, Pylint, Mypy

## Environment Variables

Key configuration variables (see `.env.example`):

- `LLM_PROVIDER` - LLM provider to use (`openai` or `local`)
- `OPENAI_API_KEY` - Your OpenAI API key (required for provider `openai`)
- `OPENAI_MODEL` - Model to use with OpenAI (default: gpt-4)
- `LOCAL_LLM_URL` - URL for a local LLM service (required for provider `local`)
- `LOCAL_LLM_MODEL` - Local model name to request from the local LLM service (default: gpt2)
- `INVESTIGATION_TIMEOUT` - Investigation timeout in seconds (default: 20)
- `AGENT_TIMEOUT` - Individual agent timeout (default: 10)
- `LOG_LEVEL` - Logging level (default: INFO)

## Future Roadmap

- **V2:** PostgreSQL database, Redis caching, real Kubernetes integration
- **V3:** GitHub integration, Cloud provider APIs, advanced monitoring
- **V4:** Marketplace for custom agents, audit logging, multi-tenancy

## License

Proprietary - Charan Valaboju

## Support

For issues or questions, please reach out to the development team.
# AI-Devops-Teams
