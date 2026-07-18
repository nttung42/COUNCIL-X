# SHB AI

A unified platform for multiple AI services (plugins), providing a unified API and infrastructure for plugin management, event-driven async job processing, and LLM integration.

## Overview

SHB AI is designed to make adding new AI services easy. Each service is a plugin that follows a standard interface, and the platform handles authentication, distributed job queuing, file storage, and LLM integration.

## Features

- **Plugin Architecture**: Add new services by creating a package following the `BaseAIService` interface
- **Event-Driven Job Processing**: Celery + Redis for fast, scalable async job processing (50x faster than polling)
- **Auto-Discovery**: Plugins are automatically discovered and registered on server startup
- **File Storage**: Built-in file upload and management with configurable storage backend
- **LLM Integration**: Abstract LLM provider (OpenAI, Anthropic, etc.) via LangChain
- **API Key Authentication**: Simple header-based API authentication
- **Docker Support**: Full Docker Compose setup with Redis for local development and production

## Tech Stack

- **FastAPI**: Async HTTP framework
- **SQLAlchemy 2.x**: Async ORM with PostgreSQL
- **PostgreSQL**: Persistent job and user storage
- **Celery 5.3+**: Distributed task queue
- **Redis 7+**: Message broker and result backend
- **LangChain/LangGraph**: LLM orchestration
- **LLM Providers**: OpenAI, Anthropic, OpenRouter (multi-provider gateway)
- **Python 3.12**: Latest stable version with enhanced performance
- **Docker Compose**: Containerized development and deployment
- **Pre-commit Hooks**: black, flake8, isort, mypy, bandit for code quality

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- PostgreSQL and Redis (or use Docker Compose)

### Local Development with Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Update .env with your API keys
# LLM_API_KEY - Get from https://openrouter.ai/keys
# Generate SECRET_KEY using: uv run python scripts/generate_secret_key.py

# Start all services (PostgreSQL, Redis, FastAPI, Celery)
docker compose up

# API is available at http://localhost:8888
# PostgreSQL is available at localhost:5433
# Redis is available at localhost:6379
```

### Local Development without Docker

```bash
# Install dependencies (requires Python 3.12+)
uv sync

# Set up environment
cp .env.example .env
# Edit .env with:
#   - LLM_API_KEY (from https://openrouter.ai/keys)
#   - DATABASE_URL
#   - CELERY_BROKER_URL and CELERY_RESULT_BACKEND (Redis URLs)
# Generate SECRET_KEY: uv run python scripts/generate_secret_key.py

# Ensure PostgreSQL and Redis are running
# PostgreSQL: postgresql://user:password@localhost/shb
# Redis: redis://localhost:6379

# Run migrations
alembic upgrade head

# Test LLM integration
uv run python scripts/test_llm_call.py

# Terminal 1: Start FastAPI server
uv run uvicorn shb.main:app --reload

# Terminal 2: Start Celery worker
uv run celery -A shb.core.celery_app worker --loglevel=info

# Terminal 3 (optional): Monitor Celery events
uv run celery -A shb.core.celery_app events
```

## API Endpoints

All endpoints require the `X-API-Key` header.

### Services (Plugins)

```bash
# List available services
curl -H "X-API-Key: your-api-key" http://localhost:8888/api/v1/services

# Get service details
curl -H "X-API-Key: your-api-key" http://localhost:8888/api/v1/services/{service_id}

# Run service synchronously
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "World"}}' \
  http://localhost:8888/api/v1/services/hello_world/run

# Response for async services: {"job_id": "uuid", "status": "pending"}
# Response for sync services: {"result": {...}}
```

### Jobs

```bash
# Get job status and results
curl -H "X-API-Key: your-api-key" http://localhost:8888/api/v1/jobs/{job_id}

# List user's jobs (paginated)
curl -H "X-API-Key: your-api-key" http://localhost:8888/api/v1/jobs

# Cancel pending job
curl -X DELETE \
  -H "X-API-Key: your-api-key" \
  http://localhost:8888/api/v1/jobs/{job_id}
```

### Files

```bash
# Upload file
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  http://localhost:8888/api/v1/files
```

## Adding a New Plugin (Service)

Plugins implement the `BaseAIService` interface. Quick summary:

1. Create plugin directory: `src/shb/ai/plugins/{plugin_id}/`

2. Implement plugin structure:

```
src/shb/ai/plugins/my_plugin/
├── __init__.py          # Package marker
├── schema.py            # Pydantic models for input/output
├── service.py           # Plugin implementation
├── graph.py             # LangGraph workflow (optional)
└── prompts/             # LLM prompts (optional)
```

3. Create the plugin class:

```python
# src/shb/ai/plugins/my_plugin/schema.py
from pydantic import BaseModel

class MyPluginInput(BaseModel):
    text: str

class MyPluginOutput(BaseModel):
    result: str

# src/shb/ai/plugins/my_plugin/service.py
from shb.ai.plugins import BaseAIService, AIServiceContext, AIServiceMeta
from shb.ai.plugins.my_plugin.schema import MyPluginInput, MyPluginOutput

class MyPlugin(BaseAIService):
    meta = AIServiceMeta(
        id="my_plugin",
        name="My Plugin",
        description="Does something useful",
        is_async=False,  # Set to True for Celery job processing
        accepts_file=False,
    )

    InputSchema = MyPluginInput
    OutputSchema = MyPluginOutput

    async def run(self, input_data: MyPluginInput, ctx: AIServiceContext) -> MyPluginOutput:
        # Your plugin logic here
        return MyPluginOutput(result=f"Processed: {input_data.text}")
```

4. Plugin is automatically discovered and registered on startup via `AIServiceRegistry.discover_and_register()`

## Architecture

### Plugin System

- **BaseAIService**: Abstract base class for plugins
- **AIServiceMeta**: Plugin metadata (id, name, description, is_async flag, etc.)
- **AIServiceContext**: Context passed to plugins (user_id, job_id, service_id, update_progress callback)
- **AIServiceRegistry**: Auto-discovers and registers plugins from `src/shb/ai/plugins/`

### Event-Driven Job Processing (Celery + Redis)

- **Synchronous Services**: Executed immediately in FastAPI request, return result synchronously
- **Asynchronous Services**:
  1. Job created in PostgreSQL with `PENDING` status
  2. Task enqueued to Redis (Celery message broker)
  3. API returns `job_id` immediately for polling
  4. Celery worker picks up from Redis queue (<100ms latency)
  5. Worker executes plugin and updates PostgreSQL job status
  6. Client polls `/api/v1/jobs/{job_id}` for results

**Performance**: Celery + Redis delivers 50x faster job pickup vs PostgreSQL polling (50ms vs 5000ms)

### File Storage

- Files uploaded via `/api/v1/files` endpoint
- Stored in `storage/` directory (configurable)
- Can be referenced by `file_id` in plugin inputs
- Abstracted behind `StorageService` for future S3/cloud storage integration

## Plugins

### doc_summary

Summarize PDF/DOCX/TXT documents using LangGraph map-reduce workflow.

- Service ID: `doc_summary`
- Type: Asynchronous (Celery job)
- Accepts files: Yes
- Input: `file_id`, optional `length` (short/medium/long), `language`

### meeting_summary

Summarize meeting transcripts and extract action items.

- Service ID: `meeting_summary`
- Type: Asynchronous (Celery job)
- Accepts files: Yes
- Input: `transcript` or `file_id`, optional `language`

## Configuration

See `.env.example` for all available configuration options.

### Database & Queue

- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql+asyncpg://user:pass@localhost/shb`)
- `CELERY_BROKER_URL`: Redis broker URL (e.g., `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND`: Redis results URL (e.g., `redis://localhost:6379/1`)
- `CELERY_WORKER_CONCURRENCY`: Number of parallel Celery workers (default: 4)

### LLM Configuration (OpenRouter)

OpenRouter provides unified access to 100+ LLM models from OpenAI, Anthropic, Google, DeepSeek, and more.

- `LLM_API_KEY`: OpenRouter API key (get from https://openrouter.ai/keys)
- `LLM_MODEL`: Model identifier (e.g., `deepseek/deepseek-v4-flash`, `anthropic/claude-3-5-sonnet-20241022`, `openai/gpt-4o`)
- `LLM_TEMPERATURE`: Model temperature for inference (0-2, default: 0.0)
- `LLM_MAX_TOKENS`: Maximum tokens in response (default: 4096)
- `LLM_TOP_P`: Nucleus sampling parameter (0-1, optional)
- `LLM_BASE_URL`: Custom base URL (optional, defaults to `https://openrouter.ai/api/v1`)
- `OPENROUTER_PROVIDER_ORDER`: Provider fallback order (comma-separated, auto-inferred from model if not set)
  - Example: `OPENROUTER_PROVIDER_ORDER=Anthropic,Google`
- `OPENROUTER_ALLOW_FALLBACKS`: Allow fallback to providers beyond the order list (default: true)
- `LLM_ENABLE_PROMPT_CACHE`: Enable prompt caching for supported providers (default: false)

### Other Settings

- `STORAGE_DIR`: Where to store uploaded files (default: `storage/`)
- `MAX_FILE_SIZE_MB`: Maximum file upload size (default: 100 MB)
- `LOG_LEVEL`: Logging level (default: INFO)
- `SECRET_KEY`: Secret key for session encryption and security (generate with `uv run python scripts/generate_secret_key.py`)

## Testing & Development Scripts

### Test LLM Integration

```bash
# Quick test of LLM integration
uv run python scripts/test_llm_call.py
```

### Generate Secret Key

```bash
# Generate a secure SECRET_KEY for production
uv run python scripts/generate_secret_key.py
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=shb

# Run specific test
uv run pytest tests/test_plugins_doc_summary.py -v

# Run with pre-commit checks
uv run pre-commit run --all-files
```

## Deployment

### Using Docker Compose

```bash
docker compose up -d
```

This starts:
- API server on port 8888
- PostgreSQL database on port 5433
- Redis on port 6379
- Celery worker for async job processing

### Production Considerations

1. **Database**: Use managed PostgreSQL service (RDS, CloudSQL, etc.)
2. **Redis/Celery**: Deploy Redis cluster and multiple Celery workers for scalability
3. **Storage**: Switch to S3 by implementing `StorageService` backend
4. **LLM**: Use production API keys and implement rate limiting
5. **Monitoring**: Add Prometheus metrics, ELK stack for logging
6. **Auth**: Consider OAuth2 or multi-tenant API key management
7. **HTTPS**: Enable TLS/SSL in production
8. **Workers**: Run multiple Celery workers for horizontal scaling

## Troubleshooting

### Celery worker not processing jobs

```bash
# Check Celery worker logs
docker compose logs celery_worker

# Check active tasks
celery -A shb.core.celery_app inspect active

# Check worker stats
celery -A shb.core.celery_app inspect stats

# Verify Redis connection
redis-cli ping  # Should return PONG
```

### Plugin not appearing in /api/v1/services

- Check logs for import errors in plugin module
- Verify plugin class inherits from `BaseAIService`
- Ensure `__init__.py` in plugin directory properly exports the service class
- Check `AIServiceRegistry.discover_and_register()` in main.py startup

### Redis connection issues

```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping

# View Redis data
redis-cli DBSIZE
redis-cli KEYS '*'
```

### File upload fails

- Check `MAX_FILE_SIZE_MB` in config (default: 100 MB)
- Verify `storage/` directory exists and is writable
- Check available disk space


## Contributing

1. Create a feature branch
2. Implement changes following code style:
   - Run `uv run pre-commit run --all-files` before committing
   - Uses: black (formatting), isort (imports), flake8 (linting), mypy (typing), bandit (security)
3. Add tests for new features
4. Submit pull request

## License

(Add your license here)
