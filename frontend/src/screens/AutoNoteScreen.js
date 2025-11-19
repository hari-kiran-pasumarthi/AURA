import React, { useState, useRef, useEffect } from "react";

export default function AutoNoteScreen() {
  const API_BASE = "https://loyal-beauty-production.up.railway.app";

  const [note, setNote] = useState("");
  const [summary, setSummary] = useState("");
  const [loadingText, setLoadingText] = useState(false);

  const [audioBlob, setAudioBlob] = useState(null);
  const [file, setFile] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcribing, setTranscribing] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // 🧩 Auth helper
  const getAuthHeaders = (isJSON = true) => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("⚠️ Please log in first!");
      window.location.href = "/login";
      return null;
    }
    return isJSON
      ? {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        }
      : {
          Authorization: `Bearer ${token}`,
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
        setRecording(false);
        clearInterval(timerRef.current);
        // stop tracks so mic is released
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      setRecording(true);
      setRecordingTime(0);
      timerRef.current = setInterval(
        () => setRecordingTime((t) => t + 1),
        1000
      );
    } catch (err) {
      alert("🎤 Microphone permission denied. Please enable it and retry.");
      console.error(err);
    }
  };

  // 🛑 Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  };

  // ⏱ Format timer
  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec < 10 ? "0" + sec : sec}`;
  };

  // ✨ Summarize Text
  const summarizeText = async () => {
    if (!note.trim()) return alert("Enter text first!");
    setLoadingText(true);
    setSaved(false);

    const headers = getAuthHeaders(true);
    if (!headers) return;

    try {
      const res = await fetch(`${API_BASE}/autonote/text`, {
        method: "POST",
        headers,
        body: JSON.stringify({ text: note }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Summarization failed");

      setSummary(formatSummary(data));
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    } finally {
      setLoadingText(false);
    }
  };

  // 🎧 Summarize Audio
  const summarizeAudio = async () => {
    if (!audioBlob) return alert("Record audio first!");
    setTranscribing(true);
    setSaved(false);

    const headers = getAuthHeaders(false);
    if (!headers) return;

    const formData = new FormData();
    formData.append("file", audioBlob, "lecture.webm");

    try {
      const res = await fetch(`${API_BASE}/autonote/audio`, {
        method: "POST",
        headers,
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Audio summarization failed");
      setSummary(formatSummary(data));
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    } finally {
      setTranscribing(false);
    }
  };

  // 📄 Summarize File
  const summarizeFile = async () => {
    if (!file) return alert("Select a file first!");
    setUploading(true);
    setSaved(false);

    const headers = getAuthHeaders(false);
    if (!headers) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/autonote/upload`, {
        method: "POST",
        headers,
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "File summarization failed");
      setSummary(formatSummary(data));
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  // 💾 Save Note
  const saveNote = async () => {
    if (!summary.trim()) return alert("Nothing to save!");
    const title = prompt("Enter note title:", "New AutoNote");
    if (!title) return;

    const headers = getAuthHeaders(true);
    if (!headers) return;

    try {
      const res = await fetch(`${API_BASE}/autonote/save`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          title,
          summary,
          transcript: "",
          highlights: [],
          bullets: [],
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Save failed");
      alert("✅ Note saved successfully!");
      setSaved(true);
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    }
  };

  // 🧾 Helper to format summaries
  const formatSummary = (data) => {
    const highlights = data.highlights?.join(", ") || "No highlights found.";
    const bullets = data.bullets?.join("\n") || "No key points.";
    return `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${highlights}\n\n🔹 Bullets:\n${bullets}`;
  };

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        padding: 20,
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      {/* 🌌 Header */}
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
          Convert your lectures and notes into smart summaries ✨
        </p>
      </div>

      {/* 🎧 Audio Recorder */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          borderRadius: 20,
          padding: 20,
          marginBottom: 30,
          textAlign: "center",
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
        }}
      >
        <h3>🎧 Audio Recorder</h3>
        <p style={{ margin: "10px 0", fontSize: 16 }}>
          {recording
            ? `⏱ Recording... (${formatTime(recordingTime)})`
            : "Press start to begin"}
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: 10 }}>
          <button
            onClick={startRecording}
            disabled={recording}
            style={btnStyle("#2563EB")}
          >
            🎙️ Start
          </button>
          <button
            onClick={stopRecording}
            disabled={!recording}
            style={btnStyle("#DC2626")}
          >
            🛑 Stop
          </button>
        </div>

        {audioBlob && (
          <>
            <audio
              controls
              src={URL.createObjectURL(audioBlob)}
              style={{ marginTop: 15, width: "100%" }}
            />
            <button
              onClick={summarizeAudio}
              disabled={transcribing}
              style={{ ...btnStyle("#22C55E"), marginTop: 10, width: "100%" }}
            >
              {transcribing ? "⏳ Transcribing..." : "✨ Summarize Audio"}
            </button>
          </>
        )}
      </div>

      {/* 📝 Text Summarization */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          borderRadius: 20,
          padding: 20,
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
            marginBottom: 10,
          }}
        />
        <button
          onClick={summarizeText}
          disabled={loadingText}
          style={{ ...btnStyle("#6C63FF"), width: "100%" }}
        >
          {loadingText ? "⏳ Summarizing..." : "✨ Summarize Text"}
        </button>
      </div>

      {/* 📄 File Summarizer */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          borderRadius: 20,
          padding: 20,
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
        }}
      >
        <h3>📄 Summarize File (PDF / TXT)</h3>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(e) => setFile(e.target.files[0])}
          style={{ marginTop: 10, color: "#EAEAF5" }}
        />
        <button
          onClick={summarizeFile}
          disabled={!file || uploading}
          style={{ ...btnStyle("#16A34A"), width: "100%", marginTop: 10 }}
        >
          {uploading ? "⏳ Processing..." : "✨ Summarize File"}
        </button>
      </div>

      {/* 📘 Summary */}
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
              width: "100%",
            }}
          >
            {saved ? "✅ Saved!" : "💾 Save Note"}
          </button>
        </div>
      )}
    </div>
  );
}

// 🔧 Button Style Helper
const btnStyle = (color) => ({
  background: color,
  color: "#fff",
  border: "none",
  borderRadius: 10,
  padding: "10px 16px",
  fontWeight: 600,
  cursor: "pointer",
  boxShadow: "0 3px 10px rgba(0,0,0,0.3)",
});
