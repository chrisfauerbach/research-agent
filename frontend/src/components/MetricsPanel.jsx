import { useState } from "react";

function formatDuration(ms) {
  if (ms == null) return "-";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTokens(n) {
  if (n == null) return "-";
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

const styles = {
  container: {
    marginTop: 24,
    border: "1px solid #e5e7eb",
    borderRadius: 10,
    background: "#f9fafb",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 16px",
    cursor: "pointer",
    userSelect: "none",
    background: "none",
    border: "none",
    width: "100%",
    fontSize: 14,
    fontWeight: 600,
    color: "#374151",
  },
  chevron: {
    fontSize: 12,
    color: "#9ca3af",
    transition: "transform 0.2s",
  },
  summaryRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px 20px",
    padding: "0 16px 14px",
    fontSize: 13,
    color: "#6b7280",
  },
  summaryItem: {
    display: "flex",
    alignItems: "center",
    gap: 4,
  },
  summaryLabel: {
    fontWeight: 600,
    color: "#374151",
  },
  details: {
    padding: "0 16px 16px",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 12,
    marginBottom: 14,
  },
  th: {
    textAlign: "left",
    padding: "6px 8px",
    borderBottom: "2px solid #e5e7eb",
    color: "#374151",
    fontWeight: 600,
    whiteSpace: "nowrap",
  },
  td: {
    padding: "5px 8px",
    borderBottom: "1px solid #f3f4f6",
    color: "#4b5563",
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: "#374151",
    marginBottom: 6,
    marginTop: 4,
  },
};

export default function MetricsPanel({ metrics }) {
  const [expanded, setExpanded] = useState(false);

  if (!metrics || (!metrics.total_llm_calls && !metrics.llm_calls?.length)) {
    return null;
  }

  return (
    <div style={styles.container}>
      <button style={styles.header} onClick={() => setExpanded(!expanded)}>
        <span>Performance Metrics</span>
        <span style={{ ...styles.chevron, transform: expanded ? "rotate(180deg)" : "none" }}>
          &#9660;
        </span>
      </button>

      {/* Summary row — always visible */}
      <div style={styles.summaryRow}>
        <div style={styles.summaryItem}>
          <span style={styles.summaryLabel}>LLM Calls:</span>
          <span>{metrics.total_llm_calls ?? 0}</span>
        </div>
        <div style={styles.summaryItem}>
          <span style={styles.summaryLabel}>Tokens:</span>
          <span>
            {formatTokens(metrics.total_prompt_tokens)} in /{" "}
            {formatTokens(metrics.total_completion_tokens)} out
          </span>
        </div>
        <div style={styles.summaryItem}>
          <span style={styles.summaryLabel}>LLM Time:</span>
          <span>{formatDuration(metrics.total_llm_time_ms)}</span>
        </div>
        <div style={styles.summaryItem}>
          <span style={styles.summaryLabel}>Tool Time:</span>
          <span>{formatDuration(metrics.total_tool_time_ms)}</span>
        </div>
        <div style={styles.summaryItem}>
          <span style={styles.summaryLabel}>Total:</span>
          <span>{formatDuration(metrics.total_research_time_ms)}</span>
        </div>
      </div>

      {/* Expandable detail tables */}
      {expanded && (
        <div style={styles.details}>
          {/* LLM Calls table */}
          {metrics.llm_calls?.length > 0 && (
            <>
              <div style={styles.sectionTitle}>LLM Calls</div>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Node</th>
                    <th style={styles.th}>Prompt Tokens</th>
                    <th style={styles.th}>Completion Tokens</th>
                    <th style={styles.th}>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.llm_calls.map((call, i) => (
                    <tr key={i}>
                      <td style={styles.td}>{call.node}</td>
                      <td style={styles.td}>{formatTokens(call.prompt_tokens)}</td>
                      <td style={styles.td}>{formatTokens(call.completion_tokens)}</td>
                      <td style={styles.td}>{formatDuration(call.duration_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {/* Tool Calls table */}
          {metrics.tool_calls?.length > 0 && (
            <>
              <div style={styles.sectionTitle}>Tool Calls</div>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Tool</th>
                    <th style={styles.th}>Query</th>
                    <th style={styles.th}>Duration</th>
                    <th style={styles.th}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.tool_calls.map((call, i) => (
                    <tr key={i}>
                      <td style={styles.td}>{call.tool_name}</td>
                      <td style={{ ...styles.td, maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {call.query}
                      </td>
                      <td style={styles.td}>{formatDuration(call.duration_ms)}</td>
                      <td style={styles.td}>{call.success ? "OK" : "Failed"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {/* Node Timings table */}
          {metrics.node_timings?.length > 0 && (
            <>
              <div style={styles.sectionTitle}>Node Timings</div>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Node</th>
                    <th style={styles.th}>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.node_timings.map((nt, i) => (
                    <tr key={i}>
                      <td style={styles.td}>{nt.node}</td>
                      <td style={styles.td}>{formatDuration(nt.duration_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </div>
  );
}
