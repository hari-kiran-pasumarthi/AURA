import React, { useState } from "react";
import { generateNotes } from "../api";

function NotesGenerator() {
  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const res = await generateNotes(topic);
      setNotes(res.data.notes || "No notes generated.");
    } catch (error) {
      setNotes("⚠️ Error: Unable to generate notes.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>📝 Notes Generator</h2>
      <input
        type="text"
        placeholder="Enter topic..."
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        style={{ width: "100%", marginBottom: 10 }}
      />
      <br />
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? "Generating..." : "Generate Notes"}
      </button>
      <div style={{ marginTop: 20 }}>
        <h3>Generated Notes:</h3>
        <p>{notes}</p>
      </div>
    </div>
  );
}

export default NotesGenerator;
