import React, { useState, useRef } from "react";

export default function AutoNoteScreen() {
  const API_BASE = "https://loyal-beauty-production.up.railway.app";

  const [note, setNote] = useState("");
  const [summary, setSummary] = useState("");
  const [loadingText, setLoadingText] = useState(false);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [listening, setListening] = useState(false);
  const [saved, setSaved] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const recognitionRef = useRef(null);

  // 🎙️ Start Recording (Speech + Audio)
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
        audioBitsPerSecond: 128000,
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      setTranscript("");
      setSummary("");

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
      };
      mediaRecorder.start(1000);
      setRecording(true);
      setListening(true);

      // 🗣️ Live Speech Recognition
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) return alert("Speech recognition not supported!");

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-IN";

      let finalTranscript = "";
      recognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const text = event.results[i][0].transcript;
          if (event.results[i].isFinal) finalTranscript += " " + text;
          else interim += text;
        }
        setTranscript(finalTranscript + " " + interim);
      };

      recognition.onend = () => {
        if (recording) recognition.start();
        else setListening(false);
      };
      recognition.start();
    } catch {
      alert("🎤 Please allow microphone access.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) mediaRecorderRef.current.stop();
    if (recognitionRef.current) recognitionRef.current.stop();
    setRecording(false);
    setListening(false);
  };

  // ✨ Summarize Text
  const handleTextSummarize = async () => {
    if (!note.trim()) return alert("Enter text first!");
    setLoadingText(true);
    setSummary("");
    setSaved(false);
    try {
      const res = await fetch(`${API_BASE}/autonote/transcribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: note }),
      });
      const data = await res.json();
      setSummary(
        `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${data.highlights.join(
          ", "
        )}\n\n🔹 Bullets:\n${data.bullets.join("\n")}`
      );
    } catch (e) {
      alert("Text summarization failed.");
    } finally {
      setLoadingText(false);
    }
  };

  // 🎧 Summarize Audio
  const handleAudioSummarize = async () => {
    if (!audioBlob) return alert("Record audio first!");
    setLoadingAudio(true);
    setSaved(false);
    const formData = new FormData();
    formData.append("file", audioBlob, "lecture.webm");
    try {
      const res = await fetch(`${API_BASE}/autonote/audio`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setTranscript(data.transcript || transcript);
      setSummary(
        `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${data.highlights.join(
          ", "
        )}\n\n🔹 Bullets:\n${data.bullets.join("\n")}`
      );
    } catch {
      alert("Audio summarization failed.");
    } finally {
      setLoadingAudio(false);
    }
  };

  // 📄 Summarize Uploaded Document
  const handleFileSummarize = async () => {
    if (!file) return alert("Please select a file first!");
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/autonote/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setSummary(
        `📋 Summary:\n${data.summary}\n\n⭐ Highlights:\n${data.highlights.join(
          ", "
        )}\n\n🔹 Bullets:\n${data.bullets.join("\n")}`
      );
    } catch {
      alert("File summarization failed.");
    } finally {
      setUploading(false);
    }
  };

  // 💾 Save Note
  const handleSaveNote = async () => {
    if (!summary.trim()) return alert("Nothing to save!");
    const title = prompt("Enter note title:", "New AutoNote");
    if (!title) return;
    const highlights = summary
      .split("⭐ Highlights:")[1]
      ?.split("🔹 Bullets:")[0]
      ?.split(",")
      ?.map((h) => h.trim()) || [];
    const bullets = summary
      .split("🔹 Bullets:")[1]
      ?.split("\n")
      ?.filter((b) => b.trim()) || [];
    const payload = { title, transcript, summary, highlights, bullets };
    try {
      await fetch(`${API_BASE}/autonote/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setSaved(true);
      alert("✅ Note saved successfully!");
    } catch {
      alert("Save failed.");
    }
  };

  // 📚 View Saved Notes
  const handleViewSavedNotes = async () => {
    try {
      const res = await fetch(`${API_BASE}/autonote/saved`);
      const data = await res.json();
      const notes = Array.isArray(data.entries) ? data.entries : [];
      alert(`📘 You have ${notes.length} saved notes!`);
      console.log("✅ Saved Notes:", notes);
    } catch (err) {
      alert("⚠️ Failed to fetch saved notes.");
      console.error(err);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 800, margin: "0 auto" }}>
      <h2>🧠 AutoNote — Text, Audio & File Summarizer</h2>

      <button
        onClick={() => {
          setNote("");
          setSummary("");
          setTranscript("");
          setAudioBlob(null);
          setSaved(false);
          setFile(null);
        }}
        style={{
          background: "#ef4444",
          color: "#fff",
          border: "none",
          padding: "8px 16px",
          borderRadius: 8,
          marginBottom: 15,
        }}
      >
        🧹 Clear All
      </button>

      {/* TEXT INPUT */}
      <div
        style={{
          background: "#f9fafb",
          padding: 20,
          borderRadius: 10,
          marginBottom: 20,
        }}
      >
        <h3>📝 Enter Your Notes</h3>
        <textarea
          placeholder="Type or paste your notes..."
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={6}
          style={{
            width: "100%",
            borderRadius: 8,
            border: "1px solid #ddd",
            padding: 10,
            fontSize: 16,
          }}
        />
        <button
          onClick={handleTextSummarize}
          disabled={loadingText}
          style={{
            marginTop: 10,
            background: loadingText ? "#93c5fd" : "#2563eb",
            color: "white",
            border: "none",
            padding: "10px 18px",
            borderRadius: 8,
          }}
        >
          {loadingText ? "⏳ Summarizing..." : "✨ Summarize Text"}
        </button>
      </div>

      {/* AUDIO RECORD */}
      <div
        style={{
          background: "#eef2ff",
          padding: 20,
          borderRadius: 10,
          marginBottom: 20,
        }}
      >
        <h3>🎙️ Record Lecture</h3>
        <button
          onClick={recording ? stopRecording : startRecording}
          style={{
            background: recording ? "#dc2626" : "#2563eb",
            color: "white",
            border: "none",
            padding: "10px 18px",
            borderRadius: 8,
            marginRight: 10,
          }}
        >
          {recording ? "🛑 Stop Recording" : "🎧 Start Recording"}
        </button>
        <button
          onClick={handleAudioSummarize}
          disabled={!audioBlob || loadingAudio}
          style={{
            background: "#16a34a",
            color: "white",
            border: "none",
            padding: "10px 18px",
            borderRadius: 8,
          }}
        >
          {loadingAudio ? "⏳ Processing..." : "✨ Summarize Audio"}
        </button>
        {listening && <p style={{ color: "red" }}>🎤 Listening...</p>}
        {transcript && (
          <div style={{ marginTop: 15 }}>
            <h4>🗒️ Transcript:</h4>
            <p
              style={{
                background: "#fff",
                border: "1px solid #ddd",
                padding: 10,
                borderRadius: 8,
                whiteSpace: "pre-wrap",
              }}
            >
              {transcript}
            </p>
          </div>
        )}
      </div>

      {/* DOCUMENT UPLOAD */}
      <div
        style={{
          background: "#f0fdf4",
          padding: 20,
          borderRadius: 10,
          marginBottom: 20,
        }}
      >
        <h3>📄 Upload a Document (TXT or PDF)</h3>
        <input
          type="file"
          accept=".txt,.pdf"
          onChange={(e) => setFile(e.target.files[0])}
          style={{ marginBottom: 10 }}
        />
        <button
          onClick={handleFileSummarize}
          disabled={!file || uploading}
          style={{
            background: uploading ? "#93c5fd" : "#16a34a",
            color: "white",
            border: "none",
            padding: "10px 18px",
            borderRadius: 8,
          }}
        >
          {uploading ? "⏳ Summarizing File..." : "✨ Summarize File"}
        </button>
      </div>

      {/* SUMMARY */}
      {summary && (
        <div
          style={{
            background: "#fff",
            padding: 20,
            borderRadius: 10,
            border: "1px solid #ddd",
          }}
        >
          <h3>📘 Final Summary</h3>
          <pre style={{ whiteSpace: "pre-wrap", color: "#333" }}>{summary}</pre>
          <button
            onClick={handleSaveNote}
            disabled={saved}
            style={{
              marginTop: 10,
              background: saved ? "#22c55e" : "#2563eb",
              color: "white",
              border: "none",
              padding: "10px 18px",
              borderRadius: 8,
            }}
          >
            {saved ? "✅ Saved!" : "💾 Save Note"}
          </button>
          <button
            onClick={handleViewSavedNotes}
            style={{
              marginLeft: 10,
              background: "#f59e0b",
              color: "white",
              border: "none",
              padding: "10px 18px",
              borderRadius: 8,
            }}
          >
            📚 View Saved Notes
          </button>
        </div>
      )}
    </div>
  );
}
