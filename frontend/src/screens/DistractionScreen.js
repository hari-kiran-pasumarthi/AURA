// src/screens/DistractionSniperScreen.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function DistractionSniperScreen() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [blocked, setBlocked] = useState([]);
  const [loading, setLoading] = useState(false);

  const runAction = async (path, successMsg, setBlockedFromResponse = true) => {
    setLoading(true);
    setMessage("⏳ Working...");
    try {
      const res = await fetch(path, { method: "POST" });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { raw: text };
      }

      if (!res.ok) {
        setMessage(`⚠️ Failed: ${data?.error || data?.raw || res.statusText}`);
        setLoading(false);
        return;
      }

      if (setBlockedFromResponse) {
        const arr =
          Array.isArray(data.blocked) && data.blocked.length > 0
            ? data.blocked
            : Array.isArray(data.kill?.killed)
            ? data.kill.killed
            : Array.isArray(data.killed)
            ? data.killed
            : data.denied || data.candidates || data.renamed || [];
        setBlocked(arr);
      }

      setMessage(successMsg);
    } catch (err) {
      console.error("Request error:", err);
      setMessage("⚠️ Network or server error");
    } finally {
      setLoading(false);
    }
  };

  const handleStartBlock = async () => {
    await runAction(
      "https://loyal-beauty-production.up.railway.app/distraction/block-simple",
      "✅ Focus Mode activated"
    );
  };

  const handleStopBlock = async () => {
    await runAction(
      "https://loyal-beauty-production.up.railway.app/distraction/rollback",
      "✅ Focus Mode ended",
      false
    );
    setBlocked([]);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
        padding: 20,
      }}
    >
      {/* 🔹 Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          background: "rgba(255, 255, 255, 0.08)",
          backdropFilter: "blur(10px)",
          borderBottom: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 15,
          padding: "12px 20px",
          boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
          marginBottom: 30,
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
        <h2 style={{ margin: 0, fontWeight: 700 }}>🧠 Distraction Sniper</h2>
      </div>

      {/* 📘 Info */}
      <p
        style={{
          color: "#C7C9E0",
          maxWidth: 600,
          lineHeight: 1.6,
          marginBottom: 30,
        }}
      >
        Activate <b>Focus Mode</b> to block distracting apps and websites.
        AURA will intelligently pause entertainment processes, rename EXEs, and
        restrict known time-wasters. Stay in the zone. 🧘‍♂️
      </p>

      {/* 🎯 Action Buttons */}
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        <button
          onClick={handleStartBlock}
          disabled={loading}
          style={{
            background: loading
              ? "rgba(239,68,68,0.3)"
              : "linear-gradient(135deg, #DC2626, #F87171)",
            color: "#fff",
            border: "none",
            borderRadius: 12,
            padding: "14px 24px",
            fontSize: 16,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            boxShadow: "0 4px 20px rgba(220,38,38,0.3)",
            transition: "transform 0.3s ease, box-shadow 0.3s ease",
          }}
          onMouseEnter={(e) => {
            if (!loading)
              e.currentTarget.style.transform = "translateY(-3px)";
          }}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
        >
          🚫 Start Focus Mode
        </button>

        <button
          onClick={handleStopBlock}
          disabled={loading}
          style={{
            background: loading
              ? "rgba(16,185,129,0.3)"
              : "linear-gradient(135deg, #10B981, #34D399)",
            color: "#fff",
            border: "none",
            borderRadius: 12,
            padding: "14px 24px",
            fontSize: 16,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            boxShadow: "0 4px 20px rgba(16,185,129,0.3)",
            transition: "transform 0.3s ease, box-shadow 0.3s ease",
          }}
          onMouseEnter={(e) => {
            if (!loading)
              e.currentTarget.style.transform = "translateY(-3px)";
          }}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
        >
          🔓 End Focus Mode
        </button>
      </div>

      {/* 💬 Status Message */}
      {message && (
        <p
          style={{
            marginTop: 25,
            background: "rgba(255,255,255,0.08)",
            padding: "12px 18px",
            borderRadius: 12,
            backdropFilter: "blur(8px)",
            display: "inline-block",
            fontWeight: 500,
            color: "#EAEAF5",
            boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
            animation: "fadeIn 0.4s ease",
          }}
        >
          {message}
        </p>
      )}

      {/* 📋 Results */}
      {blocked.length > 0 && (
        <div
          style={{
            marginTop: 30,
            background: "rgba(255,255,255,0.1)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 16,
            padding: 20,
            maxWidth: 600,
            boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
            backdropFilter: "blur(10px)",
            animation: "fadeIn 0.6s ease",
          }}
        >
          <h4 style={{ marginBottom: 12, color: "#EAEAF5" }}>
            📵 Detected / Affected Items
          </h4>
          <ul style={{ color: "#C7C9E0", lineHeight: 1.6 }}>
            {blocked.map((it, i) => {
              if (!it) return <li key={i}>Unknown</li>;
              if (typeof it === "string") return <li key={i}>{it}</li>;
              if (typeof it === "object") {
                const name =
                  it.name ||
                  it.original ||
                  it.packageFamily ||
                  JSON.stringify(it);
                return (
                  <li key={i}>
                    <strong>{name}</strong>
                    {it.pid ? <span style={{ marginLeft: 8 }}>pid: {it.pid}</span> : null}
                  </li>
                );
              }
              return <li key={i}>{String(it)}</li>;
            })}
          </ul>
        </div>
      )}

      {/* ✨ Animation Styles */}
      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>
    </div>
  );
}
