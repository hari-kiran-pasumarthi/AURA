import React, { useState } from "react";
import { quizHelper } from "../api";

function QuizHelper() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await quizHelper(question);
      setAnswer(res.data.answer || "No answer found.");
    } catch (error) {
      setAnswer("⚠️ Error: Unable to get quiz help.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>❓ Quiz Helper</h2>
      <textarea
        placeholder="Enter your quiz question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "100%", height: "100px", marginBottom: 10 }}
      />
      <br />
      <button onClick={handleAsk} disabled={loading}>
        {loading ? "Searching..." : "Get Answer"}
      </button>
      <div style={{ marginTop: 20 }}>
        <h3>Answer:</h3>
        <p>{answer}</p>
      </div>
    </div>
  );
}

export default QuizHelper;
