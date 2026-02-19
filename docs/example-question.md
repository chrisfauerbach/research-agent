# Example Research Question

**Question:** What are the best practices for deploying LLMs in production?

**Audience:** Engineer

**Constraints:**
- max_iters: 6
- timebox_minutes: 5

## How to run

```bash
# Via CLI
docker compose run --rm api python -m research_agent.cli.main \
  "What are the best practices for deploying LLMs in production?"

# Via API
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the best practices for deploying LLMs in production?"}'
```
