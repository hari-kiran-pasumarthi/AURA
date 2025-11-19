import React, { useState, useRef, useEffect } from "react";

export default function AutoNoteScreen() {
  const API_BASE = "https://loyal-beauty-production.up.railway.app";

  const [note, setNote] = useState("");
  const [summary, setSummary] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // -------------------------------
  // AUTH HELPERS
  // -------------------------------
  const getAuthHeaders = (json = true) => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please log in first!");
      window.location.href = "/login";
      return null;
    }

    return json
      ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
      : { Authorization: `Bearer ${token}` };
  };

  // -------------------------------
  // RECORDING
  // -------------------------------
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);

        // stop stream
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      setRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => t + 1);
      }, 1000);
    } catch (err) {
      alert("Mic permission denied");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
    setRecording(false);
    clearInterval(timerRef.current);
  };

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec < 10 ? "0" + sec : sec}`;
  };

  // -------------------------------
  // SUMMARIZE TEXT
  // -------------------------------
  const summarizeText = async () => {
    if (!note.trim()) return alert("Enter text first!");
    setLoading(true);

    const headers = getAuthHeaders(true);
    if (!headers) return;

    try {
      const res = await fetch(`${API_BASE}/autonote/text`, {
        method: "POST",
        headers,
        body: JSON.stringify({ text: note }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      setSummary(formatSummary(data));
    } catch (err) {
      alert(err.message);
    }

    setLoading(false);
  };

  // -------------------------------
  // SUMMARIZE AUDIO
  // -------------------------------
  const summarizeAudio = async () => {
    if (!audioBlob) return alert("Record audio first!");
    setLoading(true);

    const headers = getAuthHeaders(false);
    if (!headers) return;

    const form = new FormData();
    form.append("file", audioBlob, "audio.webm");

    try {
      const res = await fetch(`${API_BASE}/autonote/audio`, {
        method: "POST",
        headers,
        body: form,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      setSummary(formatSummary(data));
    } catch (err) {
      alert(err.message);
    }

    setLoading(false);
  };

  // -------------------------------
  // SUMMARIZE FILE
  // -------------------------------
  const summarizeFile = async () => {
    if (!file) return alert("Select a file first!");
    setLoading(true);

    const headers = getAuthHeaders(false);
    if (!headers) return;

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/autonote/upload`, {
        method: "POST",
        headers,
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      setSummary(formatSummary(data));
    } catch (err) {
      alert(err.message);
    }

    setLoading(false);
  };

  // -------------------------------
  // SAVE NOTE
  // -------------------------------
  const saveNote = async () => {
    if (!summary.trim()) return alert("Nothing to save!");

    const title = prompt("Enter title:");
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
      if (!res.ok) throw new Error(data.detail);

      alert("Saved!");
    } catch (err) {
      alert(err.message);
    }
  };

  // -------------------------------
  // FORMAT SUMMARY
  // -------------------------------
  const formatSummary = (data) => {
    const h = data.highlights?.join(", ") || "None";
    const b = data.bullets?.join("\n") || "None";

    return `Summary:\n${data.summary}\n\nHighlights:\n${h}\n\nBullets:\n${b}`;
  };

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: 20,
        background: "#10121c",
        color: "white",
      }}
    >
      <h2 style={{ textAlign: "center" }}>AURA AutoNotes</h2>

      {/* ------------ AUDIO BLOCK ------------- */}
      <div style={blockStyle}>
        <h3>🎙️ Record Audio</h3>

        <p>{recording ? `Recording... ${formatTime(recordingTime)}` : "Idle"}</p>

        <button onClick={startRecording} disabled={recording} style={btn}>
          Start
        </button>
        <button onClick={stopRecording} disabled={!recording} style={btnRed}>
          Stop
        </button>

        {audioBlob && (
          <>
            <audio controls src={URL.createObjectURL(audioBlob)} />
            <button onClick={summarizeAudio} style={btnGreen}>
              Summarize Audio
            </button>
          </>
        )}
      </div>

      {/* ------------ TEXT BLOCK ------------- */}
      <div style={blockStyle}>
        <h3>📝 Summarize Text</h3>

        <textarea
          rows={6}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          style={textBox}
          placeholder="Paste your notes..."
        />
        <button onClick={summarizeText} style={btn}>
          Summarize Text
        </button>
      </div>

      {/* ------------ FILE BLOCK ------------- */}
      <div style={blockStyle}>
        <h3>📄 Summarize File</h3>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(e) => setFile(e.target.files[0])}
          style={{ marginBottom: 10 }}
        />
        <button onClick={summarizeFile} style={btnGreen}>
          Summarize File
        </button>
      </div>

      {/* ------------ SUMMARY ------------- */}
      {summary && (
        <div style={summaryBox}>
          <h3>📘 Summary</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{summary}</pre>
          <button onClick={saveNote} style={btn}>
            Save Note
          </button>
        </div>
      )}

      {loading && <p style={{ textAlign: "center" }}>⏳ Processing...</p>}
    </div>
  );
}

// -------------------------
// STYLES
// -------------------------
const blockStyle = {
  background: "#1a1d2b",
  padding: 20,
  borderRadius: 12,
  marginTop: 20,
};

const summaryBox = {
  background: "#1a1d2b",
  padding: 20,
  borderRadius: 12,
  marginTop: 30,
};

const textBox = {
  width: "100%",
  background: "#0f111a",
  color: "white",
  borderRadius: 8,
  padding: 10,
  marginBottom: 10,
};

const btn = {
  padding: "10px 16px",
  background: "#6C63FF",
  border: "none",
  borderRadius: 8,
  color: "white",
  cursor: "pointer",
  fontWeight: 600,
  marginTop: 10,
};

const btnRed = { ...btn, background: "#d64040" };
const btnGreen = { ...btn, background: "#22c55e" };
