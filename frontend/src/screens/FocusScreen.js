import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function FocusScreen() {
  const navigate = useNavigate();

  const [seconds, setSeconds] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);
  const [sessions, setSessions] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [agentStatus, setAgentStatus] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [faceVisible, setFaceVisible] = useState(false);
  const timerRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // ✅ Agent check
  useEffect(() => {
    const checkAgent = async () => {
      try {
        const res = await fetch("https://loyal-beauty-production.up.railway.app/focus/status");
        const data = await res.json();
        setAgentStatus(data.active || false);
      } catch {
        setAgentStatus(false);
      }
    };
    checkAgent();
    const interval = setInterval(checkAgent, 5000);
    return () => clearInterval(interval);
  }, []);

  // ✅ Webcam setup
  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        streamRef.current = stream;
        setCameraActive(true);
      } catch (err) {
        console.warn("⚠️ Camera access denied or not available:", err);
        setCameraActive(false);
      }
    }
    if (isRunning) startCamera();
    else stopCamera();
    return () => stopCamera();
  }, [isRunning]);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  // ✅ Simple face visibility check (no ML — just check if camera running)
  useEffect(() => {
    let interval;
    if (cameraActive) {
      interval = setInterval(() => {
        if (videoRef.current && videoRef.current.readyState === 4) {
          setFaceVisible(true);
        } else {
          setFaceVisible(false);
        }
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [cameraActive]);

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

  // ✅ Send telemetry periodically (mock + webcam state)
  useEffect(() => {
    let telemetryInterval;
    if (isRunning) {
      telemetryInterval = setInterval(async () => {
        try {
          const telemetryData = [
            {
              keys_per_min: Math.floor(Math.random() * 100),
              mouse_clicks: Math.floor(Math.random() * 10),
              window_changes: Math.floor(Math.random() * 3),
              app: "chrome",
              is_study_app: true,
              camera_focus: faceVisible,
            },
          ];

          const res = await fetch("https://loyal-beauty-production.up.railway.app/focus/telemetry", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              // Add auth header if backend requires it:
              // Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(telemetryData),
          });

          if (!res.ok) {
            console.warn("⚠️ Telemetry send failed:", res.status);
          } else {
            console.log("✅ Telemetry sent successfully");
          }
        } catch (err) {
          console.error("❌ Telemetry error:", err);
        }
      }, 15000); // every 15 seconds
    }
    return () => telemetryInterval && clearInterval(telemetryInterval);
  }, [isRunning, faceVisible]);

  // ✅ Poll live focus updates
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
      }, 10000);
    }
    return () => poll && clearInterval(poll);
  }, [isRunning]);

  // 🔍 Analyze focus
  const handleFocusAnalysis = async () => {
    setLoading(true);
    setFeedback("Analyzing your focus...");
    try {
      const res = await fetch("https://loyal-beauty-production.up.railway.app/focus/latest");
      const data = await res.json();
      if (data.focused) {
        setFeedback(`✅ You stayed focused! ${data.reason}`);
      } else {
        setFeedback(`⚠️ You seemed distracted. ${data.reason}`);
      }
    } catch {
      setFeedback("⚠️ Could not reach focus backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSeconds(25 * 60);
    setIsRunning(false);
    setFeedback("");
    stopCamera();
  };

  const formatTime = (time) => {
    const m = String(Math.floor(time / 60)).padStart(2, "0");
    const s = String(time % 60).padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
        position: "relative",
      }}
    >
      {/* 🔹 Header */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 20,
          right: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "rgba(255,255,255,0.08)",
          padding: "10px 20px",
          borderRadius: 12,
          backdropFilter: "blur(10px)",
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
          }}
        >
          ← Back
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <img
            src="/FullLogo.jpg"
            alt="AURA Logo"
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              boxShadow: "0 0 15px rgba(182,202,255,0.3)",
            }}
          />
          <h3 style={{ margin: 0, fontWeight: 700 }}>Focus Mode</h3>
        </div>
        <div
          style={{
            background: agentStatus ? "#16A34A" : "#EF4444",
            color: "#fff",
            fontWeight: 600,
            padding: "5px 12px",
            borderRadius: 8,
            fontSize: 14,
            boxShadow: agentStatus
              ? "0 0 12px rgba(16,185,129,0.4)"
              : "0 0 12px rgba(239,68,68,0.4)",
          }}
        >
          {agentStatus ? "📡 Agent Connected" : "⚠️ Not Running"}
        </div>
      </div>

      {/* 🕒 Circular Timer */}
      <div
        style={{
          width: 240,
          height: 240,
          borderRadius: "50%",
          border: "8px solid rgba(255,255,255,0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginTop: 100,
          background: "rgba(255,255,255,0.1)",
          backdropFilter: "blur(12px)",
          boxShadow: "0 0 25px rgba(59,130,246,0.4)",
          transition: "all 0.3s ease",
        }}
      >
        <span
          style={{
            fontSize: 48,
            fontWeight: "bold",
            color: "#EAEAF5",
            fontFamily: "monospace",
            textShadow: "0 0 8px rgba(255,255,255,0.2)",
          }}
        >
          {formatTime(seconds)}
        </span>
      </div>

      {/* 🎛 Controls */}
      <div style={{ display: "flex", gap: 20, marginTop: 40 }}>
        <button
          onClick={() => setIsRunning(true)}
          disabled={isRunning}
          style={{
            ...btnStyle,
            background: "linear-gradient(135deg, #2563EB, #4F46E5)",
            opacity: isRunning ? 0.5 : 1,
          }}
        >
          ▶ Start
        </button>
        <button
          onClick={() => setIsRunning(false)}
          style={{
            ...btnStyle,
            background: "linear-gradient(135deg, #F59E0B, #FBBF24)",
          }}
        >
          ⏸ Pause
        </button>
        <button
          onClick={handleReset}
          style={{
            ...btnStyle,
            background: "linear-gradient(135deg, #EF4444, #F87171)",
          }}
        >
          🔄 Reset
        </button>
      </div>

      {/* 📹 Camera */}
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        style={{
          marginTop: 30,
          width: 200,
          height: 150,
          borderRadius: 12,
          border: "2px solid rgba(255,255,255,0.2)",
          objectFit: "cover",
          display: cameraActive ? "block" : "none",
          boxShadow: faceVisible
            ? "0 0 15px rgba(34,197,94,0.5)"
            : "0 0 15px rgba(239,68,68,0.5)",
        }}
      />

      {/* 📊 Sessions */}
      <p style={{ fontSize: 16, marginTop: 20, color: "#C7C9E0" }}>
        Sessions completed: <b>{sessions}</b>
      </p>

      {/* 💬 Feedback */}
      {feedback && (
        <div
          style={{
            marginTop: 25,
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 12,
            padding: 18,
            maxWidth: 420,
            textAlign: "center",
            color: feedback.includes("⚠️") ? "#FCA5A5" : "#86EFAC",
            boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            backdropFilter: "blur(10px)",
            animation: "fadeIn 0.6s ease",
            whiteSpace: "pre-wrap",
          }}
        >
          {loading ? "⏳ Analyzing..." : feedback}
        </div>
      )}

      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>
    </div>
  );
}

const btnStyle = {
  color: "white",
  fontWeight: 600,
  fontSize: 16,
  border: "none",
  borderRadius: 10,
  padding: "12px 25px",
  cursor: "pointer",
  boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
  transition: "transform 0.25s ease",
};
