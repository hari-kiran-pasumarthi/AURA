import React, { useState } from "react";
import { summarizeText } from "../api";

function Summarizer() {
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSummarize = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await summarizeText(text);
      setSummary(res.data.summary || "No summary generated.");
    } catch (error) {
      setSummary("⚠️ Error: Unable to summarize text.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>📚 Text Summarizer</h2>
      <textarea
        placeholder="Paste your text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ width: "100%", height: "150px", marginBottom: 10 }}
      />
      <br />
      <button onClick={handleSummarize} disabled={loading}>
        {loading ? "Summarizing..." : "Summarize"}
      </button>
      <div style={{ marginTop: 20 }}>
        <h3>Summary:</h3>
        <p>{summary}</p>
      </div>
    </div>
  );
}

export default Summarizer;
