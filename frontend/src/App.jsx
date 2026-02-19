import { useCallback, useEffect, useState } from "react";
import ResearchForm from "./components/ResearchForm";
import ReportView from "./components/ReportView";
import RunHistory from "./components/RunHistory";
import ProgressTracker from "./components/ProgressTracker";
import MetricsPanel from "./components/MetricsPanel";
import { streamResearch, listRuns, getRun } from "./api";

const MOBILE_BREAKPOINT = 768;

const styles = {
  wrapper: {
    display: "flex",
    minHeight: "100vh",
    fontFamily: "system-ui, sans-serif",
  },
  main: {
    flex: 1,
    maxWidth: 760,
    margin: "60px auto",
    padding: "0 20px",
  },
  heading: { color: "#333" },
  spinner: { marginTop: 12, color: "#666" },
  error: { marginTop: 12, color: "#dc2626" },
  backButton: {
    background: "none",
    border: "none",
    color: "#2563eb",
    cursor: "pointer",
    fontSize: 15,
    padding: "4px 0",
    marginBottom: 12,
  },
  toggleButton: {
    position: "fixed",
    top: 12,
    left: 12,
    zIndex: 1100,
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 6,
    padding: "8px 10px",
    cursor: "pointer",
    fontSize: 20,
    lineHeight: 1,
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.3)",
    zIndex: 999,
  },
  sidebarMobile: {
    position: "fixed",
    top: 0,
    left: 0,
    zIndex: 1000,
    height: "100vh",
  },
};

export default function App() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);
  const [planSteps, setPlanSteps] = useState([]);

  const [metrics, setMetrics] = useState(null);

  const [runs, setRuns] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [selectedRunData, setSelectedRunData] = useState(null);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" && window.innerWidth < MOBILE_BREAKPOINT
  );

  // Track window resize for mobile breakpoint
  useEffect(() => {
    function handleResize() {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Load run history on mount
  const refreshHistory = useCallback(async () => {
    try {
      const data = await listRuns();
      setRuns(data);
    } catch {
      // Silently fail — sidebar just stays empty
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  // Handle selecting a past run from sidebar
  async function handleSelectRun(runId) {
    if (runId === selectedRunId) return;
    setSelectedRunId(runId);
    setSelectedRunData(null);
    setReport(null);
    setError(null);
    setLoading(true);
    if (isMobile) setSidebarOpen(false);
    try {
      const data = await getRun(runId);
      setSelectedRunData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Handle "New Research" — clear selection, show form
  function handleNewResearch() {
    setSelectedRunId(null);
    setSelectedRunData(null);
    setReport(null);
    setError(null);
    setMetrics(null);
  }

  // Handle form submission
  async function handleSubmit({ question, audience, pdfFile }) {
    setSelectedRunId(null);
    setSelectedRunData(null);
    setLoading(true);
    setReport(null);
    setError(null);
    setProgress(null);
    setPlanSteps([]);
    setMetrics(null);
    try {
      const data = await streamResearch({ question, audience, pdfFile }, (eventType, eventData) => {
        if (eventType === "status") setProgress(eventData);
        if (eventType === "plan") setPlanSteps(eventData.steps || []);
        if (eventType === "complete") setMetrics(eventData.metrics || null);
      });
      setReport(data?.report || "Research completed but no report was generated.");
      refreshHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setProgress(null);
    }
  }

  // Determine which report / metrics to display
  const displayReport = selectedRunData ? selectedRunData.report : report;
  const displayMetrics = selectedRunData ? selectedRunData.metrics : metrics;

  // Sidebar component (same for both layouts, wrapped differently)
  const sidebar = (
    <RunHistory
      runs={runs}
      selectedRunId={selectedRunId}
      onSelect={handleSelectRun}
      loading={historyLoading}
    />
  );

  return (
    <div style={styles.wrapper}>
      {/* Mobile toggle button */}
      {isMobile && (
        <button
          style={styles.toggleButton}
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label="Toggle history sidebar"
        >
          &#9776;
        </button>
      )}

      {/* Mobile overlay */}
      {isMobile && sidebarOpen && (
        <div style={styles.overlay} onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar: always visible on desktop, overlay on mobile */}
      {isMobile ? (
        sidebarOpen && <div style={styles.sidebarMobile}>{sidebar}</div>
      ) : (
        sidebar
      )}

      {/* Main content */}
      <div style={styles.main}>
        <h1 style={styles.heading}>Research Agent</h1>

        {selectedRunId && (
          <button style={styles.backButton} onClick={handleNewResearch}>
            &larr; New Research
          </button>
        )}

        {!selectedRunId && (
          <ResearchForm onSubmit={handleSubmit} disabled={loading} />
        )}

        {loading && selectedRunId && <p style={styles.spinner}>Loading report...</p>}
        {loading && !selectedRunId && (
          <ProgressTracker progress={progress} planSteps={planSteps} />
        )}
        {error && <p style={styles.error}>Error: {error}</p>}
        {displayReport && <ReportView report={displayReport} />}
        {displayReport && <MetricsPanel metrics={displayMetrics} />}
      </div>
    </div>
  );
}
