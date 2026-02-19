import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import MermaidDiagram from "./MermaidDiagram";

const styles = {
  container: {
    marginTop: 24,
    background: "#f8f8f8",
    padding: 16,
    borderRadius: 8,
    lineHeight: 1.6,
  },
};

function stripWrappingFence(text) {
  // LLMs often wrap markdown output in ```markdown ... ```
  // Strip leading/trailing whitespace then remove outer fence if present
  let trimmed = text.trim();
  const match = trimmed.match(/^```(?:markdown|md)?\s*\n([\s\S]*)\n```$/);
  return match ? match[1].trim() : trimmed;
}

export default function ReportView({ report }) {
  const content = stripWrappingFence(report);

  return (
    <div style={styles.container}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const language = match ? match[1] : null;

            if (language === "mermaid") {
              return (
                <MermaidDiagram
                  chart={String(children).replace(/\n$/, "")}
                />
              );
            }

            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </Markdown>
    </div>
  );
}
