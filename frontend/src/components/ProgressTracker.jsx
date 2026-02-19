const PHASES = [
  { key: "plan", label: "Plan" },
  { key: "act", label: "Act" },
  { key: "observe", label: "Observe" },
  { key: "reflect", label: "Reflect" },
  { key: "write_report", label: "Write" },
];

const PHASE_ORDER = Object.fromEntries(PHASES.map((p, i) => [p.key, i]));

function phaseStatus(phaseKey, currentNode) {
  const current = PHASE_ORDER[currentNode] ?? -1;
  const phase = PHASE_ORDER[phaseKey];
  if (phase < current) return "done";
  if (phase === current) return "active";
  return "pending";
}

const pillColors = {
  done: { background: "#22c55e", color: "#fff" },
  active: { background: "#2563eb", color: "#fff" },
  pending: { background: "#e5e7eb", color: "#9ca3af" },
};

const styles = {
  container: {
    marginTop: 16,
    padding: 20,
    background: "#f9fafb",
    borderRadius: 10,
    border: "1px solid #e5e7eb",
  },
  pipeline: {
    display: "flex",
    alignItems: "center",
    gap: 0,
    justifyContent: "center",
    flexWrap: "wrap",
  },
  pill: {
    padding: "6px 14px",
    borderRadius: 16,
    fontSize: 13,
    fontWeight: 600,
    whiteSpace: "nowrap",
  },
  connector: {
    width: 24,
    height: 2,
    background: "#d1d5db",
    flexShrink: 0,
  },
  details: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px 20px",
    marginTop: 14,
    fontSize: 13,
    color: "#6b7280",
    justifyContent: "center",
  },
  detailItem: {
    display: "flex",
    alignItems: "center",
    gap: 4,
  },
  detailLabel: {
    fontWeight: 600,
    color: "#374151",
  },
  steps: {
    marginTop: 14,
    padding: 0,
    listStyle: "none",
    fontSize: 13,
  },
  step: {
    padding: "4px 0",
    display: "flex",
    alignItems: "flex-start",
    gap: 8,
  },
  stepIcon: {
    flexShrink: 0,
    width: 18,
    textAlign: "center",
    lineHeight: "20px",
  },
  stepDone: { color: "#22c55e" },
  stepActive: { color: "#2563eb", fontWeight: 600 },
  stepPending: { color: "#9ca3af" },
};

function StepIcon({ status }) {
  if (status === "done") return <span style={styles.stepDone}>&#10003;</span>;
  if (status === "active") return <span style={styles.stepActive}>&#9654;</span>;
  return <span style={styles.stepPending}>&#9675;</span>;
}

function stepStatus(index, currentIndex, currentNode) {
  // If we're past the act phase or writing, all steps are done
  if (currentNode === "write_report") return "done";
  if (index < currentIndex) return "done";
  if (index === currentIndex) return "active";
  return "pending";
}

export default function ProgressTracker({ progress, planSteps }) {
  if (!progress) return null;

  const currentNode = progress.node || "plan";
  const details = [];

  if (progress.iteration > 0) {
    details.push({ label: "Iteration", value: progress.iteration });
  }
  if (progress.total_steps > 0) {
    details.push({
      label: "Step",
      value: `${progress.step_index + 1} / ${progress.total_steps}`,
    });
  }
  if (progress.tool) {
    details.push({ label: "Tool", value: progress.tool });
  }
  if (progress.evidence_count > 0) {
    details.push({ label: "Evidence", value: progress.evidence_count });
  }
  if (progress.confidence > 0) {
    details.push({
      label: "Confidence",
      value: `${Math.round(progress.confidence * 100)}%`,
    });
  }

  return (
    <div style={styles.container}>
      {/* Phase pipeline */}
      <div style={styles.pipeline}>
        {PHASES.map((phase, i) => {
          const status = phaseStatus(phase.key, currentNode);
          return (
            <div key={phase.key} style={{ display: "flex", alignItems: "center" }}>
              {i > 0 && <div style={styles.connector} />}
              <div style={{ ...styles.pill, ...pillColors[status] }}>
                {phase.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Details row */}
      {details.length > 0 && (
        <div style={styles.details}>
          {details.map((d) => (
            <div key={d.label} style={styles.detailItem}>
              <span style={styles.detailLabel}>{d.label}:</span>
              <span>{d.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Plan steps */}
      {planSteps && planSteps.length > 0 && (
        <ul style={styles.steps}>
          {planSteps.map((step, i) => {
            const status = stepStatus(i, progress.step_index, currentNode);
            const textStyle =
              status === "done"
                ? styles.stepDone
                : status === "active"
                  ? styles.stepActive
                  : styles.stepPending;
            return (
              <li key={i} style={styles.step}>
                <span style={styles.stepIcon}>
                  <StepIcon status={status} />
                </span>
                <span style={textStyle}>{step}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
