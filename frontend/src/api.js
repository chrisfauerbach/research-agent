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

export async function streamResearch({ question, audience, pdfFile }, onEvent) {
  const form = new FormData();
  form.append("question", question);
  form.append("audience", audience);
  if (pdfFile) {
    form.append("pdf_file", pdfFile);
  }
  const res = await fetch(`${API_BASE}/research`, {
    method: "POST",
    headers: { Accept: "text/event-stream" },
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completeData = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Split on double-newline (SSE event boundary)
    const parts = buffer.split("\n\n");
    // Keep the last (possibly incomplete) chunk in the buffer
    buffer = parts.pop();

    for (const part of parts) {
      if (!part.trim()) continue;
      let eventType = "message";
      let dataStr = "";
      for (const line of part.split("\n")) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          dataStr = line.slice(6);
        }
      }
      if (!dataStr) continue;
      const parsed = JSON.parse(dataStr);

      if (eventType === "error") {
        throw new Error(parsed.message || "Research failed");
      }
      if (eventType === "complete") {
        completeData = parsed;
      }
      onEvent(eventType, parsed);
    }
  }

  return completeData;
}

export async function listRuns() {
  const res = await fetch(`${API_BASE}/runs`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function getRun(runId) {
  const res = await fetch(`${API_BASE}/runs/${runId}`);
  if (res.status === 404) throw new Error("Run not found");
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
