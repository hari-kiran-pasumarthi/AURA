import React, { useState, useRef } from "react";

export default function AutoNoteScreen() {
  const API_BASE = "https://loyal-beauty-production.up.railway.app";

  const [note, setNote] = useState("");
  const [summary, setSummary] = useState("");
  const [loadingText, setLoadingText] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saved, setSaved] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // 🧠 Utility: Get headers with Bearer token
  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("⚠️ Please log in first!");
      window.location.href = "/login";
      return {};
    }
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  };

  // 🎙️ Start Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
      };
      mediaRecorder.start();
      alert("🎙️ Recording started!");
    } catch (err) {
      alert("Microphone permission denied.");
    }
  };

  // 🛑 Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
    alert("Recording stopped!");
  };

  // ✨ Summarize Text
  const summarizeText = async () => {
    if (!note.trim()) return alert("Enter text first!");
    setLoadingText(true);
    try {
      const res = await fetch(`${API_BASE}/autonote/transcribe`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ text: note }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to summarize");
      setSummary(
        `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${data.highlights.join(
          ", "
        )}\n\n🔹 Bullets:\n${data.bullets.join("\n")}`
      );
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    } finally {
      setLoadingText(false);
    }
  };

  // 🎧 Summarize Audio
  const summarizeAudio = async () => {
    if (!audioBlob) return alert("Record audio first!");
    const token = localStorage.getItem("token");
    if (!token) return alert("⚠️ Please log in first!");
    const formData = new FormData();
    formData.append("file", audioBlob, "lecture.webm");

    try {
      const res = await fetch(`${API_BASE}/autonote/audio`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to summarize audio");
      setSummary(
        `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${data.highlights.join(
          ", "
        )}\n\n🔹 Bullets:\n${data.bullets.join("\n")}`
      );
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    }
  };

  // 📄 Summarize File
  const summarizeFile = async () => {
    if (!file) return alert("Select a file first!");
    const token = localStorage.getItem("token");
    if (!token) return alert("⚠️ Please log in first!");
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/autonote/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to summarize file");
      setSummary(
        `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${data.highlights.join(
          ", "
        )}\n\n🔹 Bullets:\n${data.bullets.join("\n")}`
      );
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  // 💾 Save
  const saveNote = async () => {
    if (!summary.trim()) return alert("Nothing to save!");
    const title = prompt("Enter note title:", "New AutoNote");
    if (!title) return;
    try {
      const res = await fetch(`${API_BASE}/autonote/save`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ title, summary }),
      });
      if (!res.ok) throw new Error("Save failed");
      alert("✅ Note saved successfully!");
      setSaved(true);
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        padding: 20,
        fontFamily: "'Poppins', sans-serif",
        overflowX: "hidden",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: 40 }}>
        <img
          src="/FullLogo.jpg"
          alt="AURA Logo"
          style={{
            width: 160,
            borderRadius: 20,
            boxShadow: "0 0 25px rgba(182, 202, 255, 0.3)",
          }}
        />
        <h2 style={{ marginTop: 20 }}>🧠 AURA AutoNotes</h2>
        <p style={{ color: "#C7C9E0" }}>
          Convert your study materials into smart summaries ✨
        </p>
      </div>

      {/* 📝 Text Section */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          borderRadius: 20,
          padding: 20,
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
          marginBottom: 30,
        }}
      >
        <h3>📝 Summarize Text</h3>
        <textarea
          placeholder="Type or paste your notes..."
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={6}
          style={{
            width: "100%",
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.2)",
            background: "rgba(255,255,255,0.05)",
            color: "#EAEAF5",
            padding: 10,
            fontSize: 15,
            marginTop: 10,
          }}
        />
        <button
          onClick={summarizeText}
          disabled={loadingText}
          style={{
            marginTop: 15,
            padding: "10px 16px",
            border: "none",
            borderRadius: 10,
            background: "#6C63FF",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {loadingText ? "⏳ Summarizing..." : "✨ Summarize Text"}
        </button>
      </div>

      {/* 🎧 Audio & File Section (unchanged style) */}
      {/* ... same as before, no visual change ... */}

      {summary && (
        <div
          style={{
            marginTop: 40,
            background: "rgba(255,255,255,0.1)",
            borderRadius: 20,
            padding: 20,
            boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
          }}
        >
          <h3>📘 Summary</h3>
          <pre style={{ whiteSpace: "pre-wrap", color: "#EAEAF5" }}>
            {summary}
          </pre>
          <button
            onClick={saveNote}
            style={{
              marginTop: 15,
              padding: "10px 16px",
              borderRadius: 10,
              border: "none",
              background: saved ? "#22C55E" : "#6C63FF",
              color: "#fff",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {saved ? "✅ Saved!" : "💾 Save Note"}
          </button>
        </div>
      )}
    </div>
  );
}
