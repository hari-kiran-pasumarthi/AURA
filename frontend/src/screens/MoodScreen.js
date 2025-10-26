import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Webcam from "react-webcam";

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
  const [entries, setEntries] = useState([]);
  const [savedLogs, setSavedLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detectedMood, setDetectedMood] = useState(null);

  const detectMoodFromCamera = async () => {
    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) return alert("⚠️ Could not capture image.");

    setLoading(true);
    try {
      const blob = await (await fetch(screenshot)).blob();
      const formData = new FormData();
      formData.append("image", blob, "mood.jpg");

      const res = await fetch("http://127.0.0.1:8000/mood/detect", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Detection failed");
      const data = await res.json();

      const moodLabel = data.mood.charAt(0).toUpperCase() + data.mood.slice(1);
      const matched = moods.find((m) => m.label.toLowerCase() === data.mood.toLowerCase());
      setSelectedMood(matched || { label: moodLabel, emoji: "🧠" });
      setDetectedMood(moodLabel);
    } catch (err) {
      console.error("❌ Detection error:", err);
      alert("⚠️ Mood detection failed.");
    } finally {
      setLoading(false);
    }
  };

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
      const res = await fetch("http://127.0.0.1:8000/mood/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newEntry),
      });

      if (!res.ok) throw new Error(`Server responded with ${res.status}`);
      const data = await res.json();

      setEntries((prev) => [newEntry, ...prev]);
      setSelectedMood(null);
      setNote("");
      setDetectedMood(null);
      alert("✅ Mood logged successfully!");
      console.log("💾 Saved to:", data.file_path);
      fetchSavedLogs();
    } catch (err) {
      console.error("❌ Logging failed:", err);
      alert("⚠️ Backend error. Is FastAPI running?");
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedLogs = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/mood/logs");
      if (!res.ok) throw new Error("Failed to fetch logs");
      const data = await res.json();
      console.log("✅ Logs fetched from backend:", data.logs);
      setSavedLogs(data.logs);
    } catch (err) {
      console.error("❌ Failed to load saved logs:", err);
    }
  };

  useEffect(() => {
    fetchSavedLogs();
  }, []);

  return (
    <div style={{ backgroundColor: "#f9fafb", minHeight: "100vh", padding: 20 }}>
      <button onClick={() => navigate(-1)} style={{ color: "#2563eb", background: "none", border: "none", fontSize: 16, cursor: "pointer", marginBottom: 10 }}>
        ← Back
      </button>

      <h2 style={{ fontSize: 28, fontWeight: "700", marginBottom: 15 }}>😊 Mood Tracker</h2>
      <p style={{ fontSize: 16, color: "#555", marginBottom: 10 }}>Detect your mood or select manually:</p>

      <Webcam audio={false} ref={webcamRef} screenshotFormat="image/jpeg" width={320} height={240} />
      <button onClick={detectMoodFromCamera} disabled={loading} style={{ marginTop: 10, marginBottom: 20 }}>
        {loading ? "⏳ Detecting..." : "📸 Detect Mood from Camera"}
      </button>
      {detectedMood && <p>🧠 Detected Mood: <strong>{detectedMood}</strong></p>}

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "center", marginBottom: 20 }}>
        {moods.map((m) => (
          <button
            key={m.label}
            onClick={() => setSelectedMood(m)}
            style={{
              backgroundColor: selectedMood?.label === m.label ? "#2563eb" : "#fff",
              border: `2px solid ${selectedMood?.label === m.label ? "#2563eb" : "#ddd"}`,
              borderRadius: 12,
              padding: "15px 20px",
              cursor: "pointer",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span style={{ fontSize: 28 }}>{m.emoji}</span>
            <span style={{ color: selectedMood?.label === m.label ? "#fff" : "#111", fontWeight: 600 }}>
              {m.label}
            </span>
          </button>
        ))}
      </div>

      <textarea
        placeholder="Add a short note about your day (optional)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        style={{
          width: "100%",
          backgroundColor: "#fff",
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 12,
          fontSize: 16,
          minHeight: 80,
          marginBottom: 15,
          resize: "none"
        }}
      ></textarea>

      <button
        onClick={saveMood}
        disabled={loading}
        style={{
          backgroundColor: loading ? "#93c5fd" : "#2563eb",
          color: "white",
          fontSize: 18,
          fontWeight: 600,
          border: "none",
          borderRadius: 10,
          padding: "12px 20px",
          cursor: loading ? "not-allowed" : "pointer",
          marginBottom: 20,
        }}
      >
        {loading ? "⏳ Saving..." : "💾 Save Mood"}
      </button>

      <h3 style={{ fontSize: 20, fontWeight: "700", marginBottom: 10 }}>🗓️ Mood History</h3>
      {entries.length === 0 ? (
        <p style={{ color: "#666", textAlign: "center" }}>No mood entries yet. Record how you feel today!</p>
      ) : (
        <div>
          {entries.map((item, index) => (
            <div
              key={index}
              style={{
                backgroundColor: "#fff",
                borderRadius: 10,
                padding: 15,
                border: "1px solid #ddd",
                marginBottom: 10,
              }}
            >
              <p style={{ fontSize: 18, margin: 0 }}>
                {item.emoji} {item.mood}
              </p>
              <p style={{ color: "#666", margin: "4px 0" }}>
                📅 {new Date(item.timestamp).toLocaleDateString()}
              </p>
              {item.note && <p style={{ color: "#444", marginTop: 5 }}>📝 {item.note}</p>}
            </div>
          ))}
        </div>
      )}

      <h3 style={{ fontSize: 20, fontWeight: "700", marginTop: 30, marginBottom: 10 }}>📁 Saved Mood Logs</h3>
      {savedLogs.length === 0 ? (
        <p style={{ color: "#666", textAlign: "center" }}>No saved logs found.</p>
      ) : (
        <div style={{ backgroundColor: "#fff", borderRadius: 10, padding: 15, border: "1px solid #ddd" }}>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {savedLogs.map((log, index) => (
              <li key={index} style={{ marginBottom: 8, fontSize: 16, color: "#333" }}>
                {log}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
