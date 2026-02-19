import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
});

// LLMs produce labels like [Route 53 (Latency-Based Routing)] where parens/brackets
// collide with mermaid's node-shape syntax.  Wrap those labels in quotes so mermaid
// treats the special characters as literal text.
function sanitizeChart(chart) {
  // [label with (parens)] → ["label with (parens)"]   — avoid [[...]] compound brackets
  let result = chart.replace(
    /(?<!\[)\[([^\]"]*[(){}][^\]"]*)\](?!\])/g,
    '["$1"]',
  );
  // (label with [brackets]) → ("label with [brackets]") — avoid ((...)) compound brackets
  result = result.replace(
    /(?<!\()\(([^)"]*[\[\]{}][^)"]*)\)(?!\))/g,
    '("$1")',
  );
  // {label with (parens)} → {"label with (parens)"}    — avoid {{...}} compound brackets
  result = result.replace(
    /(?<!\{)\{([^}"]*[()[\]][^}"]*)\}(?!\})/g,
    '{"$1"}',
  );
  return result;
}

// Serialize all mermaid.render() calls — concurrent calls corrupt its internal state
let renderQueue = Promise.resolve();
let renderCounter = 0;

function enqueueRender(chart) {
  const id = `mmd-${++renderCounter}-${Date.now()}`;
  const promise = renderQueue.then(async () => {
    // Clean up any orphaned temp element from a prior failed render
    document.getElementById(id)?.remove();
    const { svg, bindFunctions } = await mermaid.render(id, chart);
    return { svg, bindFunctions };
  });
  // Keep the queue moving even if this render fails
  renderQueue = promise.catch(() => {});
  return promise;
}

const styles = {
  error: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: 6,
    padding: 12,
    fontFamily: "monospace",
    fontSize: 13,
    whiteSpace: "pre-wrap",
    color: "#991b1b",
    overflowX: "auto",
  },
};

export default function MermaidDiagram({ chart }) {
  const ref = useRef(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!chart || !ref.current) return;

    let cancelled = false;
    setError(false);

    enqueueRender(sanitizeChart(chart))
      .then(({ svg, bindFunctions }) => {
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
          bindFunctions?.(ref.current);
        }
      })
      .catch((err) => {
        console.warn("Mermaid render error:", err);
        if (!cancelled) setError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [chart]);

  if (error) {
    return (
      <details>
        <summary style={{ cursor: "pointer", color: "#991b1b", fontSize: 13 }}>
          Diagram failed to render (click to view source)
        </summary>
        <pre style={styles.error}>{chart}</pre>
      </details>
    );
  }

  return <div ref={ref} />;
}
