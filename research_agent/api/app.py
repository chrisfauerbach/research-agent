"""FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from research_agent.api.routers import research

app = FastAPI(
    title="Research Agent",
    version="0.1.0",
    description="Autonomous technical research agent powered by LangGraph and Ollama.",
)

app.include_router(research.router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """<!DOCTYPE html>
<html>
<head><title>Research Agent</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<style>
  body { font-family: system-ui, sans-serif; max-width: 700px; margin: 60px auto; padding: 0 20px; }
  h1 { color: #333; }
  form { display: flex; flex-direction: column; gap: 12px; }
  input, select, button { padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; }
  button { background: #2563eb; color: white; border: none; cursor: pointer; }
  button:hover { background: #1d4ed8; }
  #result { margin-top: 24px; background: #f8f8f8; padding: 16px; border-radius: 8px; display: none; line-height: 1.6; }
  #result pre { background: #e8e8e8; padding: 12px; border-radius: 6px; overflow-x: auto; }
  #result code { font-size: 14px; }
  #result h2 { border-bottom: 1px solid #ddd; padding-bottom: 4px; }
  #result ul { padding-left: 20px; }
  .spinner { display: none; margin-top: 12px; color: #666; }
</style></head>
<body>
<h1>Research Agent</h1>
<form id="form">
  <input name="question" placeholder="Enter your research question..." required />
  <select name="audience">
    <option value="engineer">Engineer</option>
    <option value="executive">Executive</option>
  </select>
  <button type="submit">Run Research</button>
</form>
<div class="spinner" id="spinner">Researching... this may take a few minutes.</div>
<div id="result"></div>
<script>
mermaid.initialize({ startOnLoad: false, theme: 'default' });

const renderer = new marked.Renderer();
renderer.code = function({ text, lang }) {
  if (lang === 'mermaid') {
    return '<pre class="mermaid">' + text + '</pre>';
  }
  return '<pre><code>' + text + '</code></pre>';
};
marked.setOptions({ renderer });

document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const spinner = document.getElementById('spinner');
  const result = document.getElementById('result');
  spinner.style.display = 'block';
  result.style.display = 'none';
  try {
    const resp = await fetch('/api/research', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: fd.get('question'), audience: fd.get('audience')}),
    });
    const data = await resp.json();
    result.innerHTML = marked.parse(data.report || JSON.stringify(data, null, 2));
    result.style.display = 'block';
    await mermaid.run({ nodes: result.querySelectorAll('.mermaid') });
  } catch(err) {
    result.textContent = 'Error: ' + err.message;
    result.style.display = 'block';
  }
  spinner.style.display = 'none';
});
</script>
</body>
</html>"""


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
