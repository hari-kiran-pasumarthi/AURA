import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function ConfusionScreen() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [chat, setChat] = useState([
    {
      sender: "bot",
      text: "👋 Hi! I’m AURA, your concept clarifier. Ask me about any confusing topic — I’ll break it down simply for you.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const API_BASE = "https://loyal-beauty-production.up.railway.app";

  // 🧠 Send question to backend
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setChat((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/confusion/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMsg.text }),
      });

      if (!res.ok) throw new Error(`Server Error: ${res.status}`);

      const data = await res.json();
      const botReply = data.explanation || "🤖 Sorry, I couldn’t generate an explanation.";
      setChat((prev) => [...prev, { sender: "bot", text: botReply }]);
    } catch (err) {
      console.error("❌ Error:", err);
      setChat((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Could not reach the AI server. Try again later." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [chat, loading]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
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
          background: "rgba(255, 255, 255, 0.08)",
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
        <h2 style={{ margin: 0, fontWeight: 700 }}>Concept Clarifier</h2>
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
        {chat.map((msg, idx) => (
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
              border: msg.sender === "bot" ? "1px solid rgba(255,255,255,0.1)" : "none",
              boxShadow:
                msg.sender === "user"
                  ? "0 4px 20px rgba(59,130,246,0.4)"
                  : "0 4px 25px rgba(0,0,0,0.3)",
              fontSize: 16,
              lineHeight: 1.5,
              animation: "fadeIn 0.4s ease",
              whiteSpace: "pre-wrap",
            }}
          >
            {msg.text}
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
              animation: "pulse 1.5s infinite",
            }}
          >
            🤖 Explaining...
          </div>
        )}
      </div>

      {/* ✍️ Input Section */}
      <div
        style={{
          display: "flex",
          padding: 15,
          borderTop: "1px solid rgba(255,255,255,0.1)",
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          placeholder="Ask about any confusing topic..."
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
            outline: "none",
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
            transition: "transform 0.25s ease",
          }}
          onMouseEnter={(e) => {
            if (!loading) e.currentTarget.style.transform = "scale(1.05)";
          }}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>

      {/* ✨ Animations */}
      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
          }
        `}
      </style>
    </div>
  );
}
