import React from "react";
import { useNavigate } from "react-router-dom";

export default function HomeScreen() {
  const navigate = useNavigate();

  const modules = [
    { path: "/autonote", label: "Auto Notes", icon: "📝", desc: "Convert audio or text into summarized notes" },
    { path: "/focus", label: "Focus Mode", icon: "🕒", desc: "Use Pomodoro timer to boost focus" },
    { path: "/planner", label: "Study Planner", icon: "📅", desc: "Plan and schedule your study tasks" },
    { path: "/doubts", label: "Doubt Solver", icon: "💭", desc: "Ask and clarify academic doubts" },
    { path: "/flashcards", label: "Flashcards", icon: "🎴", desc: "Auto-generate flashcards for revision" },
    { path: "/mood", label: "Mood Tracker", icon: "😊", desc: "Log your study mood and reflections" },
    { path: "/braindump", label: "Brain Dump", icon: "🧠", desc: "Organize messy thoughts with AI" },
    { path: "/chatbot", label: "AI Chatbot", icon: "🤖", desc: "Chat with your AI study assistant" },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: 20,
        color: "white",
      }}
    >
      {/* 🔹 AURA LOGO */}
      <img
        src="/FullLogo.jpg"
        alt="AURA Logo"
        style={{
          width: "220px",
          borderRadius: "20px",
          marginTop: 40,
          marginBottom: 30,
          boxShadow: "0 8px 20px rgba(0,0,0,0.3)",
        }}
      />

      {/* 🔹 SAVED FOLDER CARD */}
      <div
        onClick={() => navigate("/saved")}
        style={{
          width: "100%",
          maxWidth: 900,
          backgroundColor: "rgba(255,255,255,0.15)",
          color: "white",
          borderRadius: 15,
          padding: "18px 20px",
          marginBottom: 30,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          backdropFilter: "blur(6px)",
          boxShadow: "0 4px 15px rgba(0,0,0,0.25)",
          transition: "transform 0.2s ease, box-shadow 0.2s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-3px)";
          e.currentTarget.style.boxShadow = "0 8px 18px rgba(0,0,0,0.35)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "0 4px 15px rgba(0,0,0,0.25)";
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 32 }}>📁</span>
          <div>
            <h3 style={{ margin: 0, fontSize: 20, fontWeight: "700" }}>Saved Folder</h3>
            <p style={{ margin: 0, fontSize: 14, color: "#E0E7FF" }}>
              View your saved tasks, notes, and logs
            </p>
          </div>
        </div>
        <span style={{ fontSize: 22 }}>➡️</span>
      </div>

      {/* 🔹 MODULE GRID */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 20,
          width: "100%",
          maxWidth: 900,
        }}
      >
        {modules.map((mod) => (
          <div
            key={mod.path}
            onClick={() => navigate(mod.path)}
            style={{
              backgroundColor: "rgba(255,255,255,0.1)",
              border: "1px solid rgba(255,255,255,0.2)",
              borderRadius: 15,
              padding: "20px 15px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
              cursor: "pointer",
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
              backdropFilter: "blur(5px)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-4px)";
              e.currentTarget.style.boxShadow = "0 8px 18px rgba(0,0,0,0.35)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.25)";
            }}
          >
            <div style={{ fontSize: 32, textAlign: "center", marginBottom: 10 }}>
              {mod.icon}
            </div>
            <h3
              style={{
                textAlign: "center",
                fontSize: 18,
                fontWeight: "700",
                color: "#FFF",
                marginBottom: 6,
              }}
            >
              {mod.label}
            </h3>
            <p
              style={{
                textAlign: "center",
                color: "#E5E7EB",
                fontSize: 14,
                minHeight: 40,
              }}
            >
              {mod.desc}
            </p>
          </div>
        ))}
      </div>

      {/* 🔹 FOOTER */}
      <footer
        style={{
          marginTop: "auto",
          paddingTop: 30,
          color: "#E0E7FF",
          fontSize: 13,
          textAlign: "center",
        }}
      >
        © {new Date().getFullYear()} AURA <br />
        <span style={{ color: "#BFDBFE" }}>AI-Powered Learning Platform</span>
      </footer>
    </div>
  );
}
