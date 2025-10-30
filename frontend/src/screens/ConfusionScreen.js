import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function ConfusionScreen() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setChat((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("https://loyal-beauty-production.up.railway.app/confusion/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMsg.text }),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server Error: ${res.status} - ${errText}`);
      }

      const data = await res.json();

      // ✅ The backend returns { "explanation": "...text..." }
      const aiReply = data.explanation || "🤖 No response from the AI model.";

      const botMsg = { sender: "bot", text: aiReply };
      setChat((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("❌ Error:", err);
      const botMsg = {
        sender: "bot",
        text: "⚠️ Could not connect to the explanation server. Try again later.",
      };
      setChat((prev) => [...prev, botMsg]);
    } finally {
      setLoading(false);
    }
  };

  // Auto scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chat, loading]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        backgroundColor: "#f9fafb",
      }}
    >
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        style={{
          color: "#2563eb",
          background: "none",
          border: "none",
          fontSize: 16,
          textAlign: "left",
          padding: 15,
          cursor: "pointer",
        }}
      >
        ← Back
      </button>

      {/* Title */}
      <h2
        style={{
          fontSize: 28,
          fontWeight: "700",
          textAlign: "center",
          marginBottom: 8,
        }}
      >
        🤔 Concept Clarifier
      </h2>

      <p
        style={{
          textAlign: "center",
          color: "#555",
          marginBottom: 10,
          padding: "0 20px",
        }}
      >
        Ask any confusing topic or concept. I’ll explain it step by step in
        simple language!
      </p>

      {/* Chat Window */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: 15,
          display: "flex",
          flexDirection: "column",
          justifyContent: chat.length ? "flex-start" : "center",
        }}
      >
        {chat.length === 0 ? (
          <p style={{ textAlign: "center", color: "#888", fontSize: 16 }}>
            Type your confusing topic below to get started 👇
          </p>
        ) : (
          chat.map((msg, idx) => (
            <div
              key={idx}
              style={{
                alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
                backgroundColor:
                  msg.sender === "user" ? "#2563eb" : "#e5e7eb",
                color: msg.sender === "user" ? "#fff" : "#111",
                padding: 12,
                borderRadius: 15,
                marginBottom: 10,
                maxWidth: "80%",
                fontSize: 16,
                whiteSpace: "pre-wrap",
              }}
            >
              {msg.text}
            </div>
          ))
        )}

        {loading && (
          <div style={{ textAlign: "center", color: "#2563eb" }}>
            ⏳ Explaining...
          </div>
        )}
      </div>

      {/* Input Section */}
      <div
        style={{
          display: "flex",
          borderTop: "1px solid #ddd",
          backgroundColor: "#fff",
          padding: 10,
        }}
      >
        <input
          type="text"
          placeholder="Ask about a confusing topic..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          style={{
            flex: 1,
            backgroundColor: "#f3f4f6",
            border: "none",
            borderRadius: 20,
            padding: "10px 15px",
            fontSize: 16,
            outline: "none",
          }}
        />
        <button
          onClick={sendMessage}
          style={{
            backgroundColor: "#2563eb",
            color: "white",
            border: "none",
            borderRadius: 20,
            padding: "10px 20px",
            marginLeft: 10,
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
