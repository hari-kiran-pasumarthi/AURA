import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Webcam from "react-webcam";
import API from "../api"; // ✅ import your authorized API instance

const moods = [
  { emoji: "😄", label: "Happy" },
  { emoji: "😐", label: "Neutral" },
  { emoji: "😢", label: "Sad" },
  { emoji: "😡", label: "Angry" },
  { emoji: "😴", label: "Tired" },
  { emoji: "🤩", label: "Excited" },
];

export default function MoodScreen() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const [selectedMood, setSelectedMood] = useState(null);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [detectedMood, setDetectedMood] = useState(null);
  const [savedLogs, setSavedLogs] = useState([]);

  // 🧠 Detect mood using webcam
  const detectMoodFromCamera = async () => {
    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) return alert("⚠️ Could not capture image.");

    setLoading(true);
    try {
      const blob = await (await fetch(screenshot)).blob();
      const formData = new FormData();
      formData.append("image", blob, "mood.jpg");

      const res = await API.post("/mood/detect", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = res.data;
      const moodLabel = data.mood.charAt(0).toUpperCase() + data.mood.slice(1);
      const matched = moods.find(
        (m) => m.label.toLowerCase() === data.mood.toLowerCase()
      );
      setSelectedMood(matched || { label: moodLabel, emoji: "🧠" });
      setDetectedMood(moodLabel);
    } catch (err) {
      console.error("❌ Detection error:", err);
      alert("⚠️ Mood detection failed or unauthorized.");
    } finally {
      setLoading(false);
    }
  };

  // 💾 Save mood and refresh logs
  const saveMood = async () => {
    if (!selectedMood) return alert("⚠️ Please select or detect a mood first!");

    const newEntry = {
      mood: selectedMood.label,
      emoji: selectedMood.emoji,
      note: note.trim(),
      timestamp: Date.now(),
    };

    setLoading(true);
    try {
      await API.post("/mood/log", newEntry);
      alert("✅ Mood logged successfully!");
      setSelectedMood(null);
      setNote("");
      setDetectedMood(null);
      fetchSavedLogs(); // refresh mood history
    } catch (err) {
      console.error("❌ Logging failed:", err);
      alert("⚠️ Please log in again. Your session may have expired.");
    } finally {
      setLoading(false);
    }
  };

  // 📜 Fetch user's mood logs
  const fetchSavedLogs = async () => {
    try {
      const res = await API.get("/mood/logs");
      console.log("📜 Mood logs response:", res.data);
      setSavedLogs(res.data.entries || []);
    } catch (err) {
      console.error("❌ Failed to load saved logs:", err);
    }
  };

  // Load logs on mount
  useEffect(() => {
    fetchSavedLogs();
  }, []);

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
        padding: 20,
      }}
    >
      {/* 🔹 Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          width: "100%",
          maxWidth: 800,
          justifyContent: "space-between",
          background: "rgba(255,255,255,0.08)",
          backdropFilter: "blur(10px)",
          borderRadius: 15,
          padding: "12px 20px",
          marginBottom: 20,
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
          <h3 style={{ margin: 0, fontWeight: 700 }}>Mood Tracker</h3>
        </div>
      </div>

      {/* 🎥 Webcam Section */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          padding: 20,
          borderRadius: 20,
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
          marginBottom: 20,
          textAlign: "center",
        }}
      >
        <p>🧠 Detect your mood automatically using the webcam:</p>
        <Webcam
          audio={false}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          width={320}
          height={240}
          style={{
            borderRadius: 10,
            border: "2px solid rgba(255,255,255,0.15)",
            marginBottom: 10,
          }}
        />
        <br />
        <button
          onClick={detectMoodFromCamera}
          disabled={loading}
          style={{
            background: loading
              ? "rgba(147,197,253,0.3)"
              : "linear-gradient(135deg, #2563EB, #4F46E5)",
            color: "white",
            border: "none",
            borderRadius: 10,
            padding: "10px 20px",
            fontSize: 16,
            cursor: "pointer",
            boxShadow: "0 4px 15px rgba(59,130,246,0.3)",
          }}
        >
          {loading ? "⏳ Detecting..." : "📸 Detect Mood"}
        </button>
        {detectedMood && (
          <p style={{ marginTop: 10, fontSize: 16 }}>
            🧠 Detected Mood: <strong>{detectedMood}</strong>
          </p>
        )}
      </div>

      {/* 😄 Manual Mood Selection */}
      <h3 style={{ marginBottom: 10 }}>Select Mood Manually</h3>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 10,
          justifyContent: "center",
          marginBottom: 20,
        }}
      >
        {moods.map((m) => (
          <button
            key={m.label}
            onClick={() => setSelectedMood(m)}
            style={{
              background:
                selectedMood?.label === m.label
                  ? "linear-gradient(135deg, #2563EB, #4F46E5)"
                  : "rgba(255,255,255,0.1)",
              color: selectedMood?.label === m.label ? "#fff" : "#EAEAF5",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 12,
              padding: "15px 20px",
              cursor: "pointer",
              transition: "transform 0.2s",
            }}
          >
            <span style={{ fontSize: 28 }}>{m.emoji}</span>
            <span style={{ fontWeight: 600 }}>{m.label}</span>
          </button>
        ))}
      </div>

      {/* ✍️ Note Input */}
      <textarea
        placeholder="Add a short note about your day (optional)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        style={{
          width: "100%",
          maxWidth: 500,
          background: "rgba(255,255,255,0.08)",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 10,
          padding: 12,
          color: "#EAEAF5",
          fontSize: 16,
          minHeight: 80,
          marginBottom: 15,
          resize: "none",
        }}
      />

      <button
        onClick={saveMood}
        disabled={loading}
        style={{
          background: loading
            ? "rgba(147,197,253,0.3)"
            : "linear-gradient(135deg, #2563EB, #4F46E5)",
          color: "white",
          fontSize: 18,
          fontWeight: 600,
          border: "none",
          borderRadius: 10,
          padding: "12px 20px",
          cursor: loading ? "not-allowed" : "pointer",
          boxShadow: "0 4px 20px rgba(59,130,246,0.3)",
          marginBottom: 30,
        }}
      >
        {loading ? "⏳ Saving..." : "💾 Save Mood"}
      </button>

      {/* 📁 Saved Mood Logs */}
      <div
        style={{
          width: "100%",
          maxWidth: 600,
          background: "rgba(255,255,255,0.08)",
          padding: 20,
          borderRadius: 15,
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
        }}
      >
        <h3>📁 Saved Mood Logs</h3>
        {savedLogs.length === 0 ? (
          <p style={{ color: "#C7C9E0" }}>No saved moods yet.</p>
        ) : (
          savedLogs.map((log, index) => (
            <div
              key={index}
              style={{
                background: "rgba(255,255,255,0.1)",
                borderRadius: 10,
                padding: 12,
                marginBottom: 10,
              }}
            >
              <p style={{ fontSize: 18 }}>
                {log.emoji} {log.mood}
              </p>
              <p style={{ color: "#C7C9E0", margin: "4px 0" }}>
                📅 {log.timestamp}
              </p>
              {log.note && (
                <p style={{ color: "#EAEAF5", marginTop: 5 }}>📝 {log.note}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
