import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function SavedFolderScreen() {
  const navigate = useNavigate();

  // ✅ Only the modules you care about in Saved Files
  const modules = [
    "autonote",
    "planner",
    "flashcards",
    "doubts",
    "braindump",
    "chatbot",
  ];

  const [entries, setEntries] = useState({});
  const [moodLogs, setMoodLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      const all = {};
      const token = localStorage.getItem("token");

      for (const mod of modules) {
        try {
          let url = "";

          if (mod === "doubts") {
            url =
              "https://loyal-beauty-production.up.railway.app/doubts/history";
          } else if (mod === "autonote") {
            url =
              "https://loyal-beauty-production.up.railway.app/autonote/saved";
          } else {
            url = `https://loyal-beauty-production.up.railway.app/${mod}/saved`;
          }

          const res = await fetch(url, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });
          const data = await res.json();

          let entriesData = [];

          if (mod === "doubts") {
            entriesData = Array.isArray(data.entries) ? data.entries : [];
          } else if (Array.isArray(data.entries)) {
            entriesData = data.entries;
          } else if (Array.isArray(data)) {
            // In case the backend directly returns an array
            entriesData = data;
          }

          // ✅ Tag each entry with its module and limit to latest 3–5
          all[mod] = entriesData.slice(0, 3).map((e) => ({
            ...e,
            module: mod,
          }));
        } catch (err) {
          console.warn(`⚠️ Failed to fetch ${mod}:`, err);
          all[mod] = [];
        }
      }

      setEntries(all);
      setLoading(false);
    };

    const fetchMoodLogs = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch(
          "https://loyal-beauty-production.up.railway.app/mood/logs",
          {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          }
        );
        const data = await res.json();
        setMoodLogs(Array.isArray(data.entries) ? data.entries : []);
      } catch (err) {
        console.warn("⚠️ Failed to fetch mood logs:", err);
        setMoodLogs([]);
      }
    };

    fetchAll();
    fetchMoodLogs();
  }, []);

  const getEntries = (mod) => (Array.isArray(entries[mod]) ? entries[mod] : []);

  const getSectionTitle = (mod) => {
    switch (mod) {
      case "planner":
        return "📘 AI Study Planner";
      case "doubts":
        return "❓ Doubt History";
      case "autonote":
        return "📝 AutoNotes";
      case "braindump":
        return "🧠 Brain Dump";
      case "flashcards":
        return "🎴 Flashcards";
      case "chatbot":
        return "💬 Chatbot Conversations";
      default:
        return `📘 ${mod.charAt(0).toUpperCase() + mod.slice(1)}`;
    }
  };

  const getFallbackTitle = (mod) => {
    if (mod === "braindump") return "Brain Dump";
    if (mod === "planner") return "Study Plan";
    if (mod === "autonote") return "AutoNote";
    if (mod === "doubts") return "Doubt";
    if (mod === "flashcards") return "Flashcard";
    if (mod === "chatbot") return "Chat";
    return "Saved Entry";
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
        padding: 20,
      }}
    >
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          background: "rgba(255,255,255,0.08)",
          borderRadius: 15,
          padding: "12px 20px",
          backdropFilter: "blur(10px)",
          boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
        }}
      >
        <button
          onClick={() => navigate(-1)}
          style={{
            color: "#C7C9E0",
            background: "none",
            border: "none",
            fontSize: 16,
            cursor: "pointer",
          }}
        >
          ← Back
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <img
            src="/FullLogo.jpg"
            alt="AURA Logo"
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              boxShadow: "0 0 15px rgba(182,202,255,0.3)",
            }}
          />
          <h3 style={{ margin: 0, fontWeight: 700 }}>Saved Files</h3>
        </div>
      </div>

      {loading ? (
        <p style={{ textAlign: "center", color: "#BFC2D5" }}>
          Loading saved entries...
        </p>
      ) : (
        modules.map((mod) => {
          const modEntries = getEntries(mod);
          const sectionTitle = getSectionTitle(mod);

          return (
            <div
              key={mod}
              style={{
                background: "rgba(255,255,255,0.08)",
                borderRadius: 15,
                padding: 15,
                marginBottom: 20,
                backdropFilter: "blur(10px)",
                boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
              }}
            >
              <h3 style={{ marginBottom: 10, color: "#EAEAF5" }}>
                {sectionTitle}
              </h3>

              {modEntries.length > 0 ? (
                modEntries.map((e, i) => (
                  <div
                    key={i}
                    onClick={() => setSelectedNote({ ...e, module: mod })}
                    style={{
                      background: "rgba(255,255,255,0.1)",
                      borderRadius: 10,
                      padding: 10,
                      marginBottom: 8,
                      cursor: "pointer",
                      transition: "transform 0.25s ease, box-shadow 0.25s ease",
                    }}
                  >
                    {/* TITLE (module-aware fallback) */}
                    <p style={{ margin: 0, fontWeight: 600, color: "#EAEAF5" }}>
                      {e.title ||
                        e.topic ||
                        e.question ||
                        e.organized_text?.slice(0, 40) ||
                        e.input_text?.slice(0, 40) ||
                        e.prompt?.slice(0, 40) ||
                        getFallbackTitle(mod)}
                    </p>

                    {/* CONTENT PREVIEW */}
                    <p
                      style={{
                        color: "#C7C9E0",
                        margin: "4px 0",
                        fontSize: 14,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {e.organized_text ||
                        e.input_text ||
                        e.content ||
                        e.response ||
                        e.answer ||
                        e.summary ||
                        e.ai_message ||
                        "[No content available]"}
                    </p>

                    <p style={{ fontSize: 12, color: "#A8B0D0" }}>
                      🕒 {e.timestamp || "N/A"}
                    </p>
                  </div>
                ))
              ) : (
                <p style={{ color: "#C7C9E0", fontSize: 14 }}>
                  No saved entries yet.
                </p>
              )}
            </div>
          );
        })
      )}

      {/* MOOD LOGS */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          borderRadius: 15,
          padding: 15,
          marginBottom: 20,
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
          backdropFilter: "blur(10px)",
        }}
      >
        <h3 style={{ marginBottom: 10, color: "#EAEAF5" }}>🧠 Mood Logs</h3>
        {moodLogs.length > 0 ? (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {moodLogs.map((log, i) => (
              <li
                key={i}
                style={{
                  padding: 10,
                  borderBottom: "1px solid rgba(255,255,255,0.1)",
                  color: "#EAEAF5",
                }}
              >
                <p style={{ margin: 0, fontWeight: 600 }}>
                  {log.emoji || "🧠"} {log.mood || "Unknown Mood"}
                </p>
                <p style={{ margin: "4px 0", color: "#C7C9E0" }}>
                  📝 {log.note || "[No note]"}
                </p>
                <p style={{ fontSize: 12, color: "#A8B0D0" }}>
                  🕒 {log.timestamp || "N/A"}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: "#C7C9E0" }}>No mood logs found.</p>
        )}
      </div>

      {/* MODAL */}
      {selectedNote && (
        <div
          onClick={() => setSelectedNote(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 999,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "rgba(255,255,255,0.1)",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 15,
              padding: 20,
              width: "90%",
              maxWidth: 700,
              maxHeight: "80vh",
              overflowY: "auto",
              color: "#EAEAF5",
              boxShadow: "0 8px 30px rgba(0,0,0,0.4)",
              backdropFilter: "blur(12px)",
            }}
          >
            <h2>
              {selectedNote.title ||
                selectedNote.topic ||
                selectedNote.question ||
                selectedNote.organized_text?.slice(0, 40) ||
                selectedNote.input_text?.slice(0, 40) ||
                selectedNote.prompt?.slice(0, 40) ||
                getFallbackTitle(selectedNote.module)}
            </h2>
            <p style={{ color: "#C7C9E0", fontSize: 13 }}>
              🕒 {selectedNote.timestamp || "N/A"}
            </p>

            {selectedNote.organized_text && (
              <>
                <h3>🧠 Organized Thoughts</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {selectedNote.organized_text}
                </p>
              </>
            )}

            {selectedNote.input_text && (
              <>
                <h3>✍️ Original Text</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {selectedNote.input_text}
                </p>
              </>
            )}

            {selectedNote.summary && (
              <>
                <h3>📋 Summary</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>{selectedNote.summary}</p>
              </>
            )}

            {selectedNote.response && (
              <>
                <h3>💬 AI Clarification</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {selectedNote.response}
                </p>
              </>
            )}

            {selectedNote.answer && (
              <>
                <h3>🎴 Flashcard Answer</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>{selectedNote.answer}</p>
              </>
            )}

            {selectedNote.ai_message && (
              <>
                <h3>🤖 Chatbot Reply</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {selectedNote.ai_message}
                </p>
              </>
            )}

            <button
              onClick={() => setSelectedNote(null)}
              style={{
                marginTop: 15,
                background: "linear-gradient(135deg, #2563EB, #4F46E5)",
                color: "#fff",
                border: "none",
                padding: "10px 18px",
                borderRadius: 8,
                cursor: "pointer",
                fontWeight: 600,
                boxShadow: "0 4px 15px rgba(59,130,246,0.3)",
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
