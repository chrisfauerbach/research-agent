import { useState } from "react";
import ResearchForm from "./components/ResearchForm";
import ReportView from "./components/ReportView";
import { submitResearch } from "./api";

const styles = {
  container: {
    fontFamily: "system-ui, sans-serif",
    maxWidth: 700,
    margin: "60px auto",
    padding: "0 20px",
  },
  heading: { color: "#333" },
  spinner: { marginTop: 12, color: "#666" },
  error: { marginTop: 12, color: "#dc2626" },
};

export default function App() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit({ question, audience, pdfFile }) {
    setLoading(true);
    setReport(null);
    setError(null);
    try {
      const data = await submitResearch({ question, audience, pdfFile });
      setReport(data.report || JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Research Agent</h1>
      <ResearchForm onSubmit={handleSubmit} disabled={loading} />
      {loading && (
        <p style={styles.spinner}>Researching... this may take a few minutes.</p>
      )}
      {error && <p style={styles.error}>Error: {error}</p>}
      {report && <ReportView report={report} />}
    </div>
  );
}
