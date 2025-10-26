import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function DoubtsScreen() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const scrollRef = useRef(null);

  // 🧠 Send doubt to backend
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = [
        { timestamp: Date.now(), event: "pause", context: input },
        { timestamp: Date.now(), event: "tab_switch", context: input },
      ];

      const res = await fetch("http://127.0.0.1:8000/doubts/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      const note = data.notes?.[0] || "No AI response available.";
      const [confidenceLine, ...explanation] = note.split("\n\n");

      const aiResponse = `
📘 **Doubt Analysis**
🧩 **Topic:** ${data.topics?.[0] || "N/A"}
🔍 **${confidenceLine || ""}**

💬 **Clarification:**
${explanation.join("\n\n")}
      `.trim();

      const botMsg = {
        sender: "bot",
        text: aiResponse,
        topic: data.topics?.[0] || "N/A",
        confidence: confidenceLine?.replace("Confidence: ", "") || "Unknown",
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("❌ Error fetching doubts:", error);
      const botMsg = {
        sender: "bot",
        text: "⚠️ Unable to reach backend or AI engine. Please ensure FastAPI and Ollama are running properly.",
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setLoading(false);
    }
  };

  // 💾 Save reply to backend
  const handleSave = async (msg) => {
    if (!msg || msg.sender !== "bot") return;
    setSaving(true);
    try {
      const payload = {
        topic: msg.topic || "N/A",
        response: msg.text,
        confidence: msg.confidence || "N/A",
      };

      const res = await fetch("http://127.0.0.1:8000/doubts/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Save failed");
      alert("💾 Saved successfully!");
    } catch (e) {
      console.error("⚠️ Save failed:", e);
      alert("⚠️ Failed to save reply. Check backend connection.");
    } finally {
      setSaving(false);
    }
  };

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        backgroundColor: "#f9fafb",
      }}
    >
      {/* 🔙 Back Button */}
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

      {/* Header */}
      <h2
        style={{
          fontSize: 28,
          fontWeight: "700",
          textAlign: "center",
          marginBottom: 10,
        }}
      >
        💭 Doubt Solver
      </h2>

      <p
        style={{
          textAlign: "center",
          color: "#555",
          marginBottom: 10,
          padding: "0 20px",
        }}
      >
        Ask any academic question. The AI will detect confusion and clarify it simply.
      </p>

      {/* 💬 Chat Area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "15px",
          display: "flex",
          flexDirection: "column",
          justifyContent: messages.length ? "flex-start" : "center",
        }}
      >
        {messages.length === 0 ? (
          <p style={{ textAlign: "center", color: "#888", fontSize: 16 }}>
            Ask your first doubt below 👇
          </p>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              style={{
                alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
                backgroundColor:
                  msg.sender === "user" ? "#2563eb" : "#e5e7eb",
                borderRadius: 15,
                padding: 12,
                marginBottom: 10,
                maxWidth: "80%",
                boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
                position: "relative",
              }}
            >
              <p
                style={{
                  color: msg.sender === "user" ? "#fff" : "#111",
                  fontSize: 16,
                  margin: 0,
                  whiteSpace: "pre-wrap",
                }}
              >
                {msg.text}
              </p>

              {/* 💾 Save Button */}
              {msg.sender === "bot" && (
                <button
                  onClick={() => handleSave(msg)}
                  disabled={saving}
                  style={{
                    marginTop: 8,
                    fontSize: 13,
                    backgroundColor: "#2563eb",
                    color: "white",
                    border: "none",
                    borderRadius: 8,
                    padding: "5px 10px",
                    cursor: "pointer",
                    alignSelf: "flex-end",
                  }}
                >
                  {saving ? "Saving..." : "💾 Save"}
                </button>
              )}
            </div>
          ))
        )}

        {loading && (
          <div
            style={{
              textAlign: "center",
              color: "#2563eb",
              fontStyle: "italic",
              marginTop: 10,
            }}
          >
            ⏳ Analyzing your doubt...
          </div>
        )}
      </div>

      {/* ✍️ Input Box */}
      <div
        style={{
          display: "flex",
          padding: "10px",
          borderTop: "1px solid #ddd",
          backgroundColor: "#fff",
        }}
      >
        <input
          type="text"
          placeholder="Type your doubt..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          style={{
            flex: 1,
            backgroundColor: "#f3f4f6",
            borderRadius: 20,
            border: "none",
            padding: "10px 15px",
            fontSize: 16,
            outline: "none",
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            backgroundColor: loading ? "#93c5fd" : "#2563eb",
            color: "white",
            border: "none",
            borderRadius: 20,
            padding: "10px 20px",
            marginLeft: 10,
            fontWeight: "600",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
