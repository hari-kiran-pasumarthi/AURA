import React, { useState } from "react";
import { chatbot } from "../api";

function Chatbot() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await chatbot(question); // sends { question: "..." }
      setAnswer(res.data.answer || "No response received.");
    } catch (error) {
      setAnswer("⚠️ Error: Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>💬 Study Chatbot</h2>
      <textarea
        placeholder="Ask your study question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "100%", height: "100px", marginBottom: 10 }}
      />
      <br />
      <button onClick={handleSend} disabled={loading}>
        {loading ? "Thinking..." : "Send"}
      </button>
      <div style={{ marginTop: 20 }}>
        <h3>Response:</h3>
        <p>{answer}</p>
      </div>
    </div>
  );
}

export default Chatbot;
