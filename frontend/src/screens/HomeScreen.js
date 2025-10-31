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
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        backgroundAttachment: "fixed",
        color: "#EAEAF5",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: 20,
        fontFamily: "'Poppins', sans-serif",
        overflowX: "hidden",
      }}
    >
      {/* 🌌 LOGO SECTION */}
      <img
        src="/FullLogo.jpg"
        alt="AURA Logo"
        style={{
          width: "200px",
          marginTop: 50,
          marginBottom: 30,
          borderRadius: "24px",
          boxShadow: "0 0 25px rgba(182, 202, 255, 0.3)",
          animation: "fadeIn 2s ease-in-out",
        }}
      />

      {/* 📁 SAVED FOLDER */}
      <div
        onClick={() => navigate("/saved")}
        style={{
          width: "100%",
          maxWidth: 900,
          background: "rgba(255, 255, 255, 0.08)",
          borderRadius: 20,
          padding: "18px 20px",
          marginBottom: 40,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
          transition: "transform 0.3s ease, box-shadow 0.3s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-4px)";
          e.currentTarget.style.boxShadow = "0 6px 25px rgba(200,200,255,0.25)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.3)";
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 30 }}>📁</span>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: "700", color: "#EAEAF5" }}>
              Saved Folder
            </h3>
            <p style={{ margin: 0, fontSize: 14, color: "#BFC2D5" }}>
              View your saved tasks, notes, and logs
            </p>
          </div>
        </div>
        <span style={{ fontSize: 22, color: "#BFC2D5" }}>➡️</span>
      </div>

      {/* 🪐 MODULE GRID */}
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
              background: "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: 20,
              padding: "25px 18px",
              boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
              cursor: "pointer",
              backdropFilter: "blur(10px)",
              transition: "transform 0.25s ease, box-shadow 0.25s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-5px)";
              e.currentTarget.style.boxShadow = "0 8px 25px rgba(200,200,255,0.25)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.25)";
            }}
          >
            <div style={{ fontSize: 36, textAlign: "center", marginBottom: 10 }}>
              {mod.icon}
            </div>
            <h3
              style={{
                textAlign: "center",
                fontSize: 18,
                fontWeight: "700",
                color: "#EAEAF5",
                marginBottom: 6,
              }}
            >
              {mod.label}
            </h3>
            <p
              style={{
                textAlign: "center",
                color: "#C7C9E0",
                fontSize: 14,
                minHeight: 40,
              }}
            >
              {mod.desc}
            </p>
          </div>
        ))}
      </div>

      {/* 🌙 FOOTER */}
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
        <span style={{ color: "#C7C9E0" }}>Adaptive AI Study Companion 🌙</span>
      </footer>

      {/* 🌌 Fade-in Animation */}
      <style>
        {`
          @keyframes fadeIn {
            0% { opacity: 0; transform: scale(0.9); }
            100% { opacity: 1; transform: scale(1); }
          }
        `}
      </style>
    </div>
  );
}
