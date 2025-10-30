import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function ChatbotScreen() {
  const navigate = useNavigate();
  const API_BASE = "https://loyal-beauty-production.up.railway.app";
 // ✅ Backend URL

  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "👋 Hi there! I’m your AI study assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  // ✅ Send message to FastAPI backend
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE}/chatbot/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }), // ✅ matches backend model
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      const aiResponse =
        data.answer ||
        "🤖 Sorry, I couldn’t come up with an answer this time. Try again!";

      // Add delay for realistic typing
      setTimeout(() => {
        setMessages((prev) => [...prev, { sender: "bot", text: aiResponse }]);
        setIsTyping(false);
        setLoading(false);
      }, 800);
    } catch (error) {
      console.error("❌ Chatbot error:", error);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "⚠️ Could not connect to the AI server. Please check if FastAPI is running.",
        },
      ]);
      setLoading(false);
      setIsTyping(false);
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        backgroundColor: "#f9fafb",
        fontFamily: "system-ui",
      }}
    >
      {/* 🔹 Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "15px 20px",
          backgroundColor: "#2563eb",
        }}
      >
        <button
          onClick={() => navigate(-1)}
          style={{
            color: "white",
            background: "none",
            border: "none",
            fontSize: 16,
            cursor: "pointer",
          }}
        >
          ← Back
        </button>
        <h2 style={{ color: "white", margin: 0, fontWeight: "700" }}>
          AI Chatbot
        </h2>
        <div style={{ width: 40 }}></div>
      </div>

      {/* 💬 Chat Window */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: 15,
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              backgroundColor:
                msg.sender === "user" ? "#2563eb" : "#e5e7eb",
              color: msg.sender === "user" ? "#fff" : "#111",
              borderRadius: 15,
              padding: "12px 15px",
              marginBottom: 10,
              maxWidth: "80%",
              boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
              fontSize: 16,
              lineHeight: 1.5,
            }}
          >
            {msg.text}
          </div>
        ))}

        {isTyping && (
          <div
            style={{
              alignSelf: "flex-start",
              backgroundColor: "#e5e7eb",
              borderRadius: 15,
              padding: 10,
              color: "#555",
              fontSize: 15,
              fontStyle: "italic",
            }}
          >
            🤖 Typing...
          </div>
        )}
      </div>

      {/* 🧠 Input Area */}
      <div
        style={{
          display: "flex",
          borderTop: "1px solid #ddd",
          backgroundColor: "#fff",
          padding: 10,
          alignItems: "center",
        }}
      >
        <input
          type="text"
          placeholder="Ask me anything..."
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
