import { useState } from "react";

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
};

export default function ResearchForm({ onSubmit, disabled }) {
  const [question, setQuestion] = useState("");
  const [audience, setAudience] = useState("engineer");

  function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) return;
    onSubmit({ question: question.trim(), audience });
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
      <button type="submit" disabled={disabled} style={styles.button}>
        Run Research
      </button>
    </form>
  );
}
