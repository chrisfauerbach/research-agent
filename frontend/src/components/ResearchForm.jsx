import { useRef, useState } from "react";

const styles = {
  form: { display: "flex", flexDirection: "column", gap: 12 },
  input: {
    padding: 10,
    fontSize: 16,
    border: "1px solid #ccc",
    borderRadius: 6,
  },
  select: {
    padding: 10,
    fontSize: 16,
    border: "1px solid #ccc",
    borderRadius: 6,
  },
  button: {
    padding: 10,
    fontSize: 16,
    background: "#2563eb",
    color: "white",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
  },
  fileRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  fileLabel: {
    padding: "8px 14px",
    fontSize: 14,
    background: "#f3f4f6",
    border: "1px solid #ccc",
    borderRadius: 6,
    cursor: "pointer",
  },
  fileName: {
    fontSize: 14,
    color: "#374151",
  },
  removeBtn: {
    padding: "2px 8px",
    fontSize: 13,
    background: "transparent",
    border: "1px solid #ccc",
    borderRadius: 4,
    cursor: "pointer",
    color: "#6b7280",
  },
};

export default function ResearchForm({ onSubmit, disabled }) {
  const [question, setQuestion] = useState("");
  const [audience, setAudience] = useState("engineer");
  const [pdfFile, setPdfFile] = useState(null);
  const fileInputRef = useRef(null);

  function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) return;
    onSubmit({ question: question.trim(), audience, pdfFile });
  }

  function handleFileChange(e) {
    const file = e.target.files[0];
    if (file && file.name.toLowerCase().endsWith(".pdf")) {
      setPdfFile(file);
    } else if (file) {
      alert("Please select a .pdf file");
      e.target.value = "";
    }
  }

  function handleRemoveFile() {
    setPdfFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <input
        type="text"
        placeholder="Enter your research question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        required
        disabled={disabled}
        style={styles.input}
      />
      <select
        value={audience}
        onChange={(e) => setAudience(e.target.value)}
        disabled={disabled}
        style={styles.select}
      >
        <option value="engineer">Engineer</option>
        <option value="executive">Executive</option>
      </select>
      <div style={styles.fileRow}>
        <label style={styles.fileLabel}>
          Reference PDF (optional)
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={disabled}
            style={{ display: "none" }}
          />
        </label>
        {pdfFile && (
          <>
            <span style={styles.fileName}>{pdfFile.name}</span>
            <button
              type="button"
              onClick={handleRemoveFile}
              disabled={disabled}
              style={styles.removeBtn}
            >
              Remove
            </button>
          </>
        )}
      </div>
      <button type="submit" disabled={disabled} style={styles.button}>
        Run Research
      </button>
    </form>
  );
}
