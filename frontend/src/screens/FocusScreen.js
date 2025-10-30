import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function FocusScreen() {
  const navigate = useNavigate();

  // Timer state
  const [seconds, setSeconds] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [sessions, setSessions] = useState(0);

  // Focus + Agent state
  const [feedback, setFeedback] = useState("");
  const [agentStatus, setAgentStatus] = useState(false);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);

  // ✅ Check agent connection every 5 seconds
  useEffect(() => {
    const checkAgent = async () => {
      try {
        const res = await fetch("https://loyal-beauty-production.up.railway.app/focus/status");
        if (res.ok) {
          const data = await res.json();
          setAgentStatus(data.active);
        } else {
          setAgentStatus(false);
        }
      } catch {
        setAgentStatus(false);
      }
    };
    checkAgent();
    const interval = setInterval(checkAgent, 5000);
    return () => clearInterval(interval);
  }, []);

  // ✅ Timer logic
  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        setSeconds((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            setIsRunning(false);
            setSessions((s) => s + 1);
            handleFocusAnalysis();
            alert("✅ Focus session complete! Take a short break.");
            return 25 * 60;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isRunning]);

  // ✅ Poll live focus updates ONLY while timer is running
  useEffect(() => {
    let poll;
    if (isRunning) {
      poll = setInterval(async () => {
        try {
          const res = await fetch("https://loyal-beauty-production.up.railway.app/focus/latest");
          if (res.ok) {
            const data = await res.json();
            if (data.reason) {
              setFeedback(
                data.focused
                  ? `✅ Focused: ${data.reason}`
                  : `⚠️ Distracted: ${data.reason}`
              );
            }
          }
        } catch (err) {
          console.log("⚠️ Live update error:", err);
        }
      }, 10000); // every 10s
    }

    // 🧹 stop polling when paused/reset
    return () => {
      if (poll) clearInterval(poll);
    };
  }, [isRunning]);

  // 🔍 Analyze focus at the end of a session
  const handleFocusAnalysis = async () => {
    setLoading(true);
    setFeedback("Analyzing your focus...");

    try {
      const res = await fetch("https://loyal-beauty-production.up.railway.app/focus/latest");
      if (!res.ok) throw new Error(`Backend Error: ${res.status}`);
      const data = await res.json();

      if (data.focused) {
        setFeedback(`✅ You stayed focused! ${data.reason}`);
      } else {
        setFeedback(`⚠️ You seemed distracted. ${data.reason}`);
      }
    } catch (err) {
      console.error("❌ Focus analysis error:", err);
      setFeedback("⚠️ Could not reach focus backend. Please check FastAPI.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Reset timer and feedback
  const handleReset = () => {
    setSeconds(25 * 60);
    setIsRunning(false);
    setFeedback("");
  };

  // Format mm:ss
  const formatTime = (time) => {
    const m = Math.floor(time / 60)
      .toString()
      .padStart(2, "0");
    const s = (time % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f9fafb",
        padding: 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
    >
      {/* 🔙 Back Button */}
      <button
        onClick={() => navigate(-1)}
        style={{
          position: "absolute",
          top: 20,
          left: 20,
          background: "none",
          border: "none",
          color: "#2563eb",
          fontSize: 16,
          cursor: "pointer",
        }}
      >
        ← Back
      </button>

      {/* 📡 Agent Status */}
      <div
        style={{
          position: "absolute",
          top: 20,
          right: 20,
          padding: "6px 12px",
          borderRadius: 8,
          backgroundColor: agentStatus ? "#22c55e" : "#ef4444",
          color: "white",
          fontWeight: "600",
          fontSize: 14,
        }}
      >
        {agentStatus ? "📡 Agent Connected" : "⚠️ Agent Not Running"}
      </div>

      <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 20 }}>
        🕒 Focus Mode
      </h2>

      {/* 🧭 Circular Timer */}
      <div
        style={{
          width: 200,
          height: 200,
          borderRadius: "50%",
          border: "8px solid #2563eb",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 30,
          backgroundColor: "#fff",
        }}
      >
        <span
          style={{
            fontSize: 48,
            fontWeight: "bold",
            color: "#1e3a8a",
            fontFamily: "monospace",
          }}
        >
          {formatTime(seconds)}
        </span>
      </div>

      {/* 🎛 Buttons */}
      <div style={{ display: "flex", gap: 10 }}>
        <button
          onClick={() => setIsRunning(true)}
          disabled={isRunning}
          style={{
            backgroundColor: "#2563eb",
            color: "white",
            fontSize: 18,
            fontWeight: 600,
            border: "none",
            borderRadius: 10,
            padding: "12px 25px",
            cursor: isRunning ? "not-allowed" : "pointer",
            opacity: isRunning ? 0.6 : 1,
          }}
        >
          Start
        </button>

        <button
          onClick={() => setIsRunning(false)}
          style={{
            backgroundColor: "#f59e0b",
            color: "white",
            fontSize: 18,
            fontWeight: 600,
            border: "none",
            borderRadius: 10,
            padding: "12px 25px",
            cursor: "pointer",
          }}
        >
          Pause
        </button>

        <button
          onClick={handleReset}
          style={{
            backgroundColor: "#ef4444",
            color: "white",
            fontSize: 18,
            fontWeight: 600,
            border: "none",
            borderRadius: 10,
            padding: "12px 25px",
            cursor: "pointer",
          }}
        >
          Reset
        </button>
      </div>

      {/* 📊 Sessions */}
      <p style={{ fontSize: 16, marginTop: 30, color: "#555" }}>
        Sessions completed: {sessions}
      </p>

      {/* 💬 Focus Feedback */}
      {feedback && (
        <div
          style={{
            marginTop: 20,
            backgroundColor: "#fff",
            border: "1px solid #ddd",
            borderRadius: 10,
            padding: 15,
            maxWidth: 400,
            boxShadow: "0 3px 8px rgba(0,0,0,0.05)",
            textAlign: "center",
          }}
        >
          <p
            style={{
              fontSize: 16,
              color: feedback.includes("⚠️") ? "#b91c1c" : "#15803d",
              whiteSpace: "pre-wrap",
            }}
          >
            {loading ? "⏳ Analyzing..." : feedback}
          </p>
        </div>
      )}
    </div>
  );
}
