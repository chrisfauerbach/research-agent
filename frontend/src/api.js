const API_BASE = "/api";

export async function submitResearch({ question, audience, pdfFile }) {
  const form = new FormData();
  form.append("question", question);
  form.append("audience", audience);
  if (pdfFile) {
    form.append("pdf_file", pdfFile);
  }
  const res = await fetch(`${API_BASE}/research`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function listRuns() {
  const res = await fetch(`${API_BASE}/runs`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function getRun(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
