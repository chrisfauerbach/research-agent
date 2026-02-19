import { useEffect, useRef } from "react";
import { marked } from "marked";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });

marked.use({
  renderer: {
    code({ text, lang }) {
      if (lang === "mermaid") {
        return `<pre class="mermaid">${text}</pre>`;
      }
      const escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      const cls = lang ? ` class="language-${lang}"` : "";
      return `<pre><code${cls}>${escaped}</code></pre>`;
    },
  },
});

const styles = {
  container: {
    marginTop: 24,
    background: "#f8f8f8",
    padding: 16,
    borderRadius: 8,
    lineHeight: 1.6,
  },
};

export default function ReportView({ report }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = marked.parse(report);

    const mermaidNodes = containerRef.current.querySelectorAll(".mermaid");
    if (mermaidNodes.length > 0) {
      mermaid.run({ nodes: mermaidNodes }).catch((err) => {
        console.warn("Mermaid render error:", err);
      });
    }
  }, [report]);

  return <div ref={containerRef} style={styles.container} />;
}
