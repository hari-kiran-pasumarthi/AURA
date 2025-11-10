import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api"; // ✅ import your authorized Axios instance

export default function BrainDumpScreen() {
  const navigate = useNavigate();

  const [thoughts, setThoughts] = useState("");
  const [organized, setOrganized] = useState("");
  const [filePath, setFilePath] = useState("");
  const [loading, setLoading] = useState(false);

  // 🧠 Send text to backend for organization (with auth)
  const handleOrganize = async () => {
    if (!thoughts.trim()) return alert("⚠️ Please write your thoughts first!");

    setLoading(true);
    setOrganized("");
    setFilePath("");

    try {
      // ✅ Authorized API call (token auto-attached by interceptor)
      const res = await API.post("/braindump/save", { text: thoughts });

      const data = res.data;
      setOrganized(data.organized_text || "🧠 AI couldn’t organize your text.");
      setFilePath(data.file_path || "");
    } catch (err) {
      console.error("❌ Request failed:", err);
      alert("⚠️ Could not save. Please log in again — your session may have expired.");
    } finally {
      setLoading(false);
    }
  };

  // 💾 Save locally (client-side)
  const handleSave = () => {
    if (!thoughts.trim() && !organized.trim()) return alert("⚠️ Nothing to save!");
    alert("✅ Your brain dump has been saved successfully!");
    setThoughts("");
    setOrganized("");
    setFilePath("");
  };

  // 🧹 Clear inputs
  const handleClear = () => {
    setThoughts("");
    setOrganized("");
    setFilePath("");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        backgroundAttachment: "fixed",
        color: "#EAEAF5",
        padding: 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      {/* 🔙 Back Button */}
      <button
        onClick={() => navigate(-1)}
        style={{
          alignSelf: "flex-start",
          color: "#C7C9E0",
          background: "none",
          border: "none",
          fontSize: 16,
          cursor: "pointer",
          marginBottom: 20,
          transition: "color 0.3s ease",
        }}
        onMouseEnter={(e) => (e.target.style.color = "#A5B4FC")}
        onMouseLeave={(e) => (e.target.style.color = "#C7C9E0")}
      >
        ← Back
      </button>

      {/* 🌌 Logo Header */}
      <div style={{ textAlign: "center", marginBottom: 30 }}>
        <img
          src="/FullLogo.jpg"
          alt="AURA Logo"
          style={{
            width: 160,
            borderRadius: 20,
            boxShadow: "0 0 25px rgba(182, 202, 255, 0.3)",
          }}
        />
        <h2 style={{ marginTop: 15, color: "#EAEAF5" }}>🧠 AURA Brain Dump</h2>
        <p style={{ color: "#C7C9E0", maxWidth: 500, margin: "10px auto" }}>
          Empty your mind. Organize your thoughts. Boost your focus.
        </p>
      </div>

      {/* ✍️ Input Section */}
      <div
        style={{
          width: "100%",
          maxWidth: 800,
          background: "rgba(255, 255, 255, 0.08)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: 20,
          padding: 25,
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
          backdropFilter: "blur(10px)",
          marginBottom: 30,
        }}
      >
        <h3 style={{ marginBottom: 10, color: "#EAEAF5" }}>✍️ Write Your Thoughts</h3>
        <textarea
          placeholder="Start typing your thoughts here..."
          value={thoughts}
          onChange={(e) => setThoughts(e.target.value)}
          rows={8}
          style={{
            width: "100%",
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: 10,
            padding: 15,
            color: "#EAEAF5",
            fontSize: 16,
            fontFamily: "inherit",
            outline: "none",
            resize: "vertical",
          }}
        />

        {/* 💾 Save & 🧹 Clear Buttons */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 20,
            gap: 10,
          }}
        >
          <button
            onClick={handleSave}
            style={{
              flex: 1,
              background: "#16A34A",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "12px 20px",
              fontSize: 16,
              fontWeight: 600,
              cursor: "pointer",
              transition: "background 0.3s ease",
            }}
            onMouseEnter={(e) => (e.target.style.background = "#22C55E")}
            onMouseLeave={(e) => (e.target.style.background = "#16A34A")}
          >
            💾 Save
          </button>

          <button
            onClick={handleClear}
            style={{
              flex: 1,
              background: "#DC2626",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "12px 20px",
              fontSize: 16,
              fontWeight: 600,
              cursor: "pointer",
              transition: "background 0.3s ease",
            }}
            onMouseEnter={(e) => (e.target.style.background = "#EF4444")}
            onMouseLeave={(e) => (e.target.style.background = "#DC2626")}
          >
            🧹 Clear
          </button>
        </div>
      </div>

      {/* 🧩 Organize Button */}
      <button
        onClick={handleOrganize}
        disabled={loading}
        style={{
          background: loading ? "rgba(147,197,253,0.3)" : "#2563EB",
          color: "#fff",
          border: "none",
          borderRadius: 12,
          padding: "15px 25px",
          fontSize: 18,
          fontWeight: 600,
          cursor: loading ? "not-allowed" : "pointer",
          width: "100%",
          maxWidth: 800,
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
          backdropFilter: "blur(10px)",
          transition: "transform 0.25s ease, box-shadow 0.25s ease",
          marginBottom: 30,
        }}
        onMouseEnter={(e) => {
          if (!loading) {
            e.currentTarget.style.transform = "translateY(-3px)";
            e.currentTarget.style.boxShadow = "0 8px 25px rgba(100,149,237,0.4)";
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.3)";
        }}
      >
        {loading ? "⏳ Organizing..." : "🧩 Organize My Thoughts"}
      </button>

      {/* ✨ AI Output Section */}
      {organized && (
        <div
          style={{
            width: "100%",
            maxWidth: 800,
            background: "rgba(255,255,255,0.1)",
            borderRadius: 20,
            padding: 25,
            border: "1px solid rgba(255,255,255,0.1)",
            backdropFilter: "blur(10px)",
            boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
            animation: "fadeIn 1s ease-in-out",
          }}
        >
          <h3 style={{ fontSize: 20, color: "#EAEAF5", marginBottom: 10 }}>
            ✨ AI-Organized Thoughts
          </h3>
          <p style={{ color: "#C7C9E0", whiteSpace: "pre-line", fontSize: 16 }}>
            {organized}
          </p>
          {filePath && (
            <p
              style={{
                color: "#A8B0D0",
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

      <footer
        style={{
          marginTop: "auto",
          paddingTop: 40,
          color: "#A8B0D0",
          fontSize: 14,
          textAlign: "center",
        }}
      >
        © {new Date().getFullYear()} AURA <br />
        <span style={{ color: "#C7C9E0" }}>Mind Clarity Assistant 🌙</span>
      </footer>

      <style>
        {`
          @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(10px); }
            100% { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>
    </div>
  );
}
