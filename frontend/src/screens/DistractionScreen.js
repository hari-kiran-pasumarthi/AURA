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
      // try parse JSON, fallback to raw text
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

      // normalize blocked items if present
      if (setBlockedFromResponse) {
        const arr =
          Array.isArray(data.blocked) && data.blocked.length > 0
            ? data.blocked
            : Array.isArray(data.kill?.killed)
            ? data.kill.killed
            : Array.isArray(data.kill?.killed?.killed)
            ? data.kill.killed.killed
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

  // Buttons call the backend endpoints you added earlier
  const handleStartBlock = async () => {
    // endpoint that runs kill_and_rename + hosts blocking
    await runAction("https://loyal-beauty-production.up.railway.app/distraction/block-simple", "✅ Focus Mode activated");
  };

  const handleStopBlock = async () => {
    // endpoint that runs rollback_distraction_blocker.ps1
    await runAction("https://loyal-beauty-production.up.railway.app/distraction/rollback", "✅ Focus Mode ended", false);
    setBlocked([]);
  };

  return (
    <div style={styles.container}>
      <button onClick={() => navigate(-1)} style={styles.backBtn}>
        ← Back
      </button>

      <h2 style={styles.title}>🧠 Distraction Sniper</h2>
      <p style={styles.text}>
        Activate <b>Focus Mode</b> to block entertainment apps (kill processes, rename EXEs, block domains).
      </p>

      <div style={styles.actions}>
        <button onClick={handleStartBlock} style={styles.blockBtn} disabled={loading}>
          🚫 Start Focus Mode
        </button>
        <button onClick={handleStopBlock} style={styles.unblockBtn} disabled={loading}>
          🔓 End Focus Mode
        </button>
      </div>

      {message && <p style={styles.message}>{message}</p>}

      {blocked && blocked.length > 0 && (
        <div style={styles.resultBox}>
          <h4>📵 Detected / Affected Items</h4>
          <ul>
            {blocked.map((it, i) => {
              if (!it) return <li key={i}>Unknown</li>;
              if (typeof it === "string") return <li key={i}>{it}</li>;
              // object rendering for normalized shapes
              if (typeof it === "object") {
                const name = it.name || it.original || it.packageFamily || JSON.stringify(it);
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
    </div>
  );
}

const styles = {
  container: { backgroundColor: "#f9fafb", minHeight: "100vh", padding: 20 },
  backBtn: { border: "none", background: "none", color: "#2563eb", fontSize: 16, cursor: "pointer" },
  title: { fontSize: 28, fontWeight: 700, marginTop: 10 },
  text: { color: "#555", marginTop: 8, maxWidth: 480 },
  actions: { display: "flex", gap: 10, marginTop: 20 },
  blockBtn: { backgroundColor: "#ef4444", color: "white", border: "none", borderRadius: 8, padding: "12px 20px", fontSize: 16, cursor: "pointer" },
  unblockBtn: { backgroundColor: "#10b981", color: "white", border: "none", borderRadius: 8, padding: "12px 20px", fontSize: 16, cursor: "pointer" },
  message: { marginTop: 15, color: "#111", fontWeight: 500 },
  resultBox: { marginTop: 20, background: "#fff", borderRadius: 8, padding: 12, border: "1px solid #ddd" },
};
