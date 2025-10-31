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
        background: "linear-gradient(160deg, #F8E8EE 0%, #E8F3FF 50%, #F3E8FF 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: 20,
        color: "#444",
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      {/* 🌸 AURA LOGO */}
      <img
        src="/FullLogo.jpg"
        alt="AURA Logo"
        style={{
          width: "200px",
          borderRadius: "24px",
          marginTop: 40,
          marginBottom: 25,
          boxShadow: "0 6px 15px rgba(0,0,0,0.1)",
          transition: "transform 0.4s ease",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.04)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1.0)")}
      />

      {/* 📁 SAVED FOLDER */}
      <div
        onClick={() => navigate("/saved")}
        style={{
          width: "100%",
          maxWidth: 900,
          backgroundColor: "rgba(255, 255, 255, 0.7)",
          color: "#333",
          borderRadius: 20,
          padding: "18px 20px",
          marginBottom: 30,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          boxShadow: "0 6px 20px rgba(180,180,180,0.25)",
          transition: "transform 0.25s ease, box-shadow 0.25s ease",
          backdropFilter: "blur(10px)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-3px)";
          e.currentTarget.style.boxShadow = "0 8px 25px rgba(160,160,160,0.3)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "0 6px 20px rgba(180,180,180,0.25)";
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 30 }}>📁</span>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: "700", color: "#333" }}>
              Saved Folder
            </h3>
            <p style={{ margin: 0, fontSize: 14, color: "#666" }}>
              View your saved tasks, notes, and logs
            </p>
          </div>
        </div>
        <span style={{ fontSize: 22, color: "#666" }}>➡️</span>
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
        {modules.map((mod, index) => (
          <div
            key={mod.path}
            onClick={() => navigate(mod.path)}
            style={{
              backgroundColor: "rgba(255,255,255,0.75)",
              border: "1px solid rgba(200,200,200,0.2)",
              borderRadius: 20,
              padding: "25px 18px",
              boxShadow: "0 6px 15px rgba(180,180,180,0.25)",
              cursor: "pointer",
              transition: "transform 0.25s ease, box-shadow 0.25s ease",
              backdropFilter: "blur(10px)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-5px)";
              e.currentTarget.style.boxShadow = "0 10px 25px rgba(160,160,160,0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 6px 15px rgba(180,180,180,0.25)";
            }}
          >
            <div style={{ fontSize: 36, textAlign: "center", marginBottom: 12 }}>
              {mod.icon}
            </div>
            <h3
              style={{
                textAlign: "center",
                fontSize: 18,
                fontWeight: "700",
                color: "#333",
                marginBottom: 6,
              }}
            >
              {mod.label}
            </h3>
            <p
              style={{
                textAlign: "center",
                color: "#555",
                fontSize: 14,
                minHeight: 40,
              }}
            >
              {mod.desc}
            </p>
          </div>
        ))}
      </div>

      {/* 🌷 FOOTER */}
      <footer
        style={{
          marginTop: "auto",
          paddingTop: 40,
          color: "#777",
          fontSize: 14,
          textAlign: "center",
        }}
      >
        © {new Date().getFullYear()} AURA <br />
        <span style={{ color: "#9CA3AF" }}>Adaptive AI Study Companion 🌸</span>
      </footer>
    </div>
  );
}
