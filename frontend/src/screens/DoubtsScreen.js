import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api"; // ✅ centralized axios instance with auth

export default function DoubtsScreen() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "💭 Hi, I’m AURA Doubt Solver. Ask me any concept you’re confused about — I’ll clarify it for you!",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const scrollRef = useRef(null);

  // 🧠 Send a doubt to the backend
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // ✅ Backend expects { question: "..." }
      const res = await API.post("/doubts/report", { question: userMsg.text });
      const data = res.data;

      const aiResponse = `
📘 **AURA Clarification**
🧩 **Topic:** ${data.question || "General"}
💬 ${data.response || "No detailed explanation provided."}
      `.trim();

      const botMsg = {
        sender: "bot",
        text: aiResponse,
        topic: data.question || "General",
        confidence: data.confidence || "N/A",
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("❌ Doubt fetch error:", error);
      const botMsg = {
        sender: "bot",
        text:
          "⚠️ Unable to connect to backend or unauthorized. Please log in again or check server connection.",
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setLoading(false);
    }
  };

  // 💾 Save clarification
  const handleSave = async (msg) => {
    if (!msg || msg.sender !== "bot") return;
    setSaving(true);
    try {
      const payload = {
        topic: msg.topic,
        response: msg.text,
        confidence: msg.confidence,
      };
      await API.post("/doubts/save", payload);
      alert("✅ Clarification saved successfully!");
    } catch (e) {
      console.error("⚠️ Save failed:", e);
      alert("⚠️ Failed to save reply. Please check backend connection.");
    } finally {
      setSaving(false);
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      {/* 🔹 Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "12px 20px",
          background: "rgba(255,255,255,0.08)",
          backdropFilter: "blur(10px)",
          borderBottom: "1px solid rgba(255,255,255,0.1)",
          boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
        }}
      >
        <button
          onClick={() => navigate(-1)}
          style={{
            color: "#C7C9E0",
            background: "none",
            border: "none",
            fontSize: 16,
            cursor: "pointer",
            marginRight: 15,
          }}
        >
          ← Back
        </button>
        <img
          src="/FullLogo.jpg"
          alt="AURA Logo"
          style={{
            width: 45,
            height: 45,
            borderRadius: 10,
            marginRight: 12,
            boxShadow: "0 0 15px rgba(182,202,255,0.3)",
          }}
        />
        <h2 style={{ margin: 0, fontWeight: 700 }}>Doubt Solver</h2>
      </div>

      {/* 💬 Chat Window */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: 20,
          display: "flex",
          flexDirection: "column",
          scrollBehavior: "smooth",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              background:
                msg.sender === "user"
                  ? "linear-gradient(135deg, #2563EB, #4F46E5)"
                  : "rgba(255,255,255,0.08)",
              color: msg.sender === "user" ? "#fff" : "#EAEAF5",
              borderRadius:
                msg.sender === "user"
                  ? "18px 18px 4px 18px"
                  : "18px 18px 18px 4px",
              padding: "12px 16px",
              marginBottom: 12,
              maxWidth: "80%",
              boxShadow:
                msg.sender === "user"
                  ? "0 4px 20px rgba(59,130,246,0.4)"
                  : "0 4px 20px rgba(0,0,0,0.3)",
              fontSize: 16,
              lineHeight: 1.5,
              whiteSpace: "pre-wrap",
            }}
          >
            {msg.text}
            {msg.sender === "bot" && (
              <button
                onClick={() => handleSave(msg)}
                disabled={saving}
                style={{
                  marginTop: 10,
                  background: saving
                    ? "rgba(37,99,235,0.5)"
                    : "linear-gradient(135deg, #2563EB, #4F46E5)",
                  color: "white",
                  border: "none",
                  borderRadius: 8,
                  padding: "6px 10px",
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                {saving ? "Saving..." : "💾 Save"}
              </button>
            )}
          </div>
        ))}

        {loading && (
          <div
            style={{
              alignSelf: "flex-start",
              background: "rgba(255,255,255,0.08)",
              borderRadius: "18px 18px 18px 4px",
              padding: "10px 14px",
              color: "#C7C9E0",
              fontSize: 15,
              fontStyle: "italic",
            }}
          >
            🤖 Analyzing your doubt...
          </div>
        )}
      </div>

      {/* ✍️ Input */}
      <div
        style={{
          display: "flex",
          padding: 15,
          borderTop: "1px solid rgba(255,255,255,0.1)",
          background: "rgba(255,255,255,0.05)",
          backdropFilter: "blur(10px)",
          alignItems: "center",
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
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
            color: "#EAEAF5",
            borderRadius: 20,
            padding: "12px 15px",
            fontSize: 16,
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            background: loading
              ? "rgba(147,197,253,0.3)"
              : "linear-gradient(135deg, #2563EB, #4F46E5)",
            color: "white",
            border: "none",
            borderRadius: 20,
            padding: "10px 22px",
            marginLeft: 10,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
