const UNITS = [
  { label: "second", seconds: 60 },
  { label: "minute", seconds: 3600 },
  { label: "hour", seconds: 86400 },
  { label: "day", seconds: 2592000 },
  { label: "month", seconds: 31536000 },
  { label: "year", seconds: Infinity },
];

function formatRelativeTime(isoString) {
  if (!isoString) return "";
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000;
  if (diff < 10) return "just now";
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  for (const unit of UNITS) {
    if (Math.abs(diff) < unit.seconds) {
      const prev = UNITS[UNITS.indexOf(unit) - 1];
      const divisor = prev ? prev.seconds : 1;
      return rtf.format(-Math.round(diff / divisor), unit.label);
    }
  }
  return rtf.format(-Math.round(diff / 31536000), "year");
}

const styles = {
  sidebar: {
    width: 280,
    minWidth: 280,
    height: "100vh",
    background: "#f9fafb",
    borderRight: "1px solid #e5e7eb",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  header: {
    padding: "20px 16px 12px",
    fontSize: 14,
    fontWeight: 600,
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  list: {
    flex: 1,
    overflowY: "auto",
    padding: 0,
    margin: 0,
    listStyle: "none",
  },
  item: {
    padding: "12px 16px",
    cursor: "pointer",
    borderLeft: "3px solid transparent",
    borderBottom: "1px solid #f3f4f6",
    transition: "background 0.15s",
  },
  itemSelected: {
    padding: "12px 16px",
    cursor: "pointer",
    borderLeft: "3px solid #2563eb",
    borderBottom: "1px solid #f3f4f6",
    background: "#e0edff",
  },
  question: {
    fontSize: 14,
    color: "#1f2937",
    margin: 0,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  time: {
    fontSize: 12,
    color: "#9ca3af",
    marginTop: 4,
  },
  empty: {
    padding: 16,
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
  },
  loading: {
    padding: 16,
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
  },
};

export default function RunHistory({ runs, selectedRunId, onSelect, loading }) {
  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>History</div>
      {loading && <div style={styles.loading}>Loading...</div>}
      {!loading && runs.length === 0 && (
        <div style={styles.empty}>No past runs yet.</div>
      )}
      {!loading && runs.length > 0 && (
        <ul style={styles.list}>
          {runs.map((run) => (
            <li
              key={run.run_id}
              style={
                run.run_id === selectedRunId ? styles.itemSelected : styles.item
              }
              onClick={() => onSelect(run.run_id)}
            >
              <p style={styles.question}>
                {run.question.length > 80
                  ? run.question.slice(0, 80) + "..."
                  : run.question}
              </p>
              <div style={styles.time}>
                {formatRelativeTime(run.created_at)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
