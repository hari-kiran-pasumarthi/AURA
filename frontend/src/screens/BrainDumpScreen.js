import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function BrainDumpScreen() {
  const navigate = useNavigate();
  const API_BASE = "https://loyal-beauty-production.up.railway.app"; // ✅ Backend URL

  const [thoughts, setThoughts] = useState("");
  const [organized, setOrganized] = useState("");
  const [filePath, setFilePath] = useState("");
  const [loading, setLoading] = useState(false);

  // 🧠 Handle organize request
  const handleOrganize = async () => {
    if (!thoughts.trim()) {
      alert("⚠️ Please write your thoughts first!");
      return;
    }

    setLoading(true);
    setOrganized("");
    setFilePath("");

    try {
      const res = await fetch(`${API_BASE}/braindump/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: thoughts }),
      });

      if (!res.ok) throw new Error(`Backend error: ${res.status}`);

      const data = await res.json();
      setOrganized(data.organized_text || "🧠 AI couldn't generate a response.");
      setFilePath(data.file_path || "");
    } catch (error) {
      console.error("❌ Backend request failed:", error);
      alert("❌ Could not reach the backend. Please ensure FastAPI is running.");
    } finally {
      setLoading(false);
    }
  };

  // 💾 Simulated Save (frontend-only reset)
  const handleSave = () => {
    if (!thoughts.trim() && !organized.trim()) {
      alert("⚠️ Nothing to save!");
      return;
    }
    alert("✅ Your brain dump has been saved successfully!");
    setThoughts("");
    setOrganized("");
    setFilePath("");
  };

  // 🧹 Clear all fields
  const handleClear = () => {
    setThoughts("");
    setOrganized("");
    setFilePath("");
  };

  return (
    <div
      style={{
        backgroundColor: "#f9fafb",
        minHeight: "100vh",
        padding: 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        fontFamily: "system-ui",
      }}
    >
      {/* 🔙 Back Button */}
      <button
        onClick={() => navigate(-1)}
        style={{
          alignSelf: "flex-start",
          color: "#2563eb",
          background: "none",
          border: "none",
          fontSize: 16,
          cursor: "pointer",
          marginBottom: 10,
        }}
      >
        ← Back
      </button>

      <h2 style={{ fontSize: 28, fontWeight: "700", marginBottom: 15 }}>
        🧠 Brain Dump
      </h2>

      <p
        style={{
          color: "#555",
          textAlign: "center",
          maxWidth: 500,
          marginBottom: 15,
        }}
      >
        Write down everything that’s on your mind — tasks, worries, ideas, or
        distractions. Then let AI help you organize it into clear, actionable thoughts.
      </p>

      {/* ✍️ Input Box */}
      <textarea
        placeholder="Start typing your thoughts here..."
        value={thoughts}
        onChange={(e) => setThoughts(e.target.value)}
        rows={8}
        style={{
          width: "100%",
          maxWidth: 600,
          backgroundColor: "#fff",
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 15,
          fontSize: 16,
          fontFamily: "inherit",
          marginBottom: 15,
          outline: "none",
          resize: "vertical",
        }}
      />

      {/* 💾 Save & 🗑 Clear Buttons */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          width: "100%",
          maxWidth: 600,
          marginBottom: 20,
          gap: 10,
        }}
      >
        <button
          onClick={handleSave}
          style={{
            flex: 1,
            backgroundColor: "#16a34a",
            color: "white",
            border: "none",
            borderRadius: 10,
            padding: "12px 20px",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          💾 Save
        </button>

        <button
          onClick={handleClear}
          style={{
            flex: 1,
            backgroundColor: "#ef4444",
            color: "white",
            border: "none",
            borderRadius: 10,
            padding: "12px 20px",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          🗑 Clear
        </button>
      </div>

      {/* 🧩 Organize Button */}
      <button
        onClick={handleOrganize}
        disabled={loading}
        style={{
          backgroundColor: loading ? "#93c5fd" : "#2563eb",
          color: "white",
          border: "none",
          borderRadius: 10,
          padding: "15px 25px",
          fontSize: 18,
          fontWeight: 600,
          cursor: loading ? "not-allowed" : "pointer",
          width: "100%",
          maxWidth: 600,
          marginBottom: 20,
        }}
      >
        {loading ? "⏳ Organizing..." : "🧩 Organize My Thoughts"}
      </button>

      {/* 🧠 Organized Output */}
      {organized && (
        <div
          style={{
            width: "100%",
            maxWidth: 600,
            backgroundColor: "#fff",
            border: "1px solid #ddd",
            borderRadius: 10,
            padding: 15,
            boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
          }}
        >
          <h3 style={{ fontSize: 20, fontWeight: "700", marginBottom: 5 }}>
            ✨ AI Summary
          </h3>
          <p
            style={{
              color: "#333",
              fontSize: 16,
              margin: 0,
              whiteSpace: "pre-line",
            }}
          >
            {organized}
          </p>

          {filePath && (
            <p
              style={{
                color: "#777",
                fontSize: 14,
                marginTop: 10,
                wordBreak: "break-all",
              }}
            >
              💾 Saved at: <b>{filePath}</b>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
