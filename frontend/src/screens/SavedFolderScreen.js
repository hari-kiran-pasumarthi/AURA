import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function SavedFolderScreen() {
  const navigate = useNavigate();

  // Removed "mood" from modules list
  const modules = [
    "autonote",
    "planner",
    "focus",
    "flashcards",
    "confusion",
    "timepredict",
    "doubts",
  ];

  const [entries, setEntries] = useState({});
  const [moodLogs, setMoodLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      const all = {};
      for (const mod of modules) {
        try {
          const url =
            mod === "doubts"
              ? "http://127.0.0.1:8000/doubts/history"
              : `http://127.0.0.1:8000/notes/list/${mod}`;

          const res = await fetch(url);
          const data = await res.json();

          if (mod === "doubts") {
            all[mod] = Array.isArray(data) ? data.slice(0, 3) : [];
          } else {
            all[mod] = Array.isArray(data.entries)
              ? data.entries.slice(0, 3)
              : [];
          }
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
        const res = await fetch("http://127.0.0.1:8000/mood/logs");
        const data = await res.json();
        console.log("✅ Mood logs fetched:", data.logs);
        setMoodLogs(Array.isArray(data.logs) ? data.logs : []);
      } catch (err) {
        console.warn("⚠️ Failed to fetch mood logs:", err);
        setMoodLogs([]);
      }
    };

    fetchAll();
    fetchMoodLogs();
  }, []);

  const getEntries = (mod) => (Array.isArray(entries[mod]) ? entries[mod] : []);

  return (
    <div style={{ backgroundColor: "#f9fafb", minHeight: "100vh", padding: 20 }}>
      <button
        onClick={() => navigate(-1)}
        style={{
          color: "#2563eb",
          background: "none",
          border: "none",
          fontSize: 16,
          cursor: "pointer",
          marginBottom: 15,
        }}
      >
        ← Back
      </button>

      <h2 style={{ fontSize: 28, fontWeight: "700", marginBottom: 20 }}>
        📁 Saved Files
      </h2>

      {loading ? (
        <p style={{ color: "#555" }}>Loading saved entries...</p>
      ) : (
        modules.map((mod) => {
          const modEntries = getEntries(mod);
          const sectionTitle =
            mod === "planner"
              ? "📘 AI Study Planner"
              : mod === "doubts"
              ? "❓ Doubt History"
              : `📘 ${mod}`;

          return (
            <div
              key={mod}
              style={{
                backgroundColor: "#fff",
                border: "1px solid #ddd",
                borderRadius: 12,
                padding: 15,
                marginBottom: 15,
                boxShadow: "0 2px 6px rgba(0,0,0,0.05)",
              }}
            >
              <h3 style={{ marginBottom: 10, color: "#111" }}>{sectionTitle}</h3>

              {modEntries.length > 0 ? (
                modEntries.map((e, i) => (
                  <div
                    key={i}
                    onClick={() => setSelectedNote({ ...e, module: mod })}
                    style={{
                      backgroundColor: "#f3f4f6",
                      borderRadius: 8,
                      padding: 10,
                      marginBottom: 6,
                      cursor: "pointer",
                      transition: "background 0.2s",
                    }}
                    onMouseEnter={(ev) =>
                      (ev.currentTarget.style.backgroundColor = "#e5e7eb")
                    }
                    onMouseLeave={(ev) =>
                      (ev.currentTarget.style.backgroundColor = "#f3f4f6")
                    }
                  >
                    <p style={{ margin: 0, fontWeight: 600 }}>
                      {e.title || e.topic || "Untitled"}
                    </p>
                    <p
                      style={{
                        color: "#555",
                        margin: 0,
                        fontSize: 14,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {e.content ||
                        e.response ||
                        e.summary ||
                        "[No content available]"}
                    </p>
                    <p style={{ fontSize: 12, color: "#888" }}>
                      🕒 {e.timestamp || "N/A"}
                    </p>
                  </div>
                ))
              ) : (
                <p style={{ color: "#999", fontSize: 14 }}>
                  No saved entries yet.
                </p>
              )}
            </div>
          );
        })
      )}

      {/* 🧠 Mood Logs Section (kept as requested) */}
      <div
        style={{
          backgroundColor: "#fff",
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 15,
          marginBottom: 15,
          boxShadow: "0 2px 6px rgba(0,0,0,0.05)",
        }}
      >
        <h3 style={{ marginBottom: 10, color: "#111" }}>🧠 Mood Logs</h3>
        {moodLogs.length > 0 ? (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {moodLogs.map((log, index) => {
              const parts = log.split(" | ");
              const timestamp = parts[0] || "N/A";
              const mood = parts[1] || "🧠 Unknown";
              const note = parts[2] || "[No note]";
              return (
                <li
                  key={index}
                  style={{
                    marginBottom: 12,
                    padding: 10,
                    borderBottom: "1px solid #eee",
                  }}
                >
                  <p style={{ margin: 0, fontWeight: 600 }}>{mood}</p>
                  <p style={{ margin: "4px 0", color: "#555" }}>{note}</p>
                  <p style={{ fontSize: 12, color: "#888" }}>🕒 {timestamp}</p>
                </li>
              );
            })}
          </ul>
        ) : (
          <p style={{ color: "#999", fontSize: 14 }}>No mood logs found.</p>
        )}
      </div>

      {/* 🔍 View Full Note Popup */}
      {selectedNote && (
        <div
          onClick={() => setSelectedNote(null)}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 999,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#fff",
              borderRadius: 10,
              padding: 20,
              width: "90%",
              maxWidth: 700,
              maxHeight: "80vh",
              overflowY: "auto",
              boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
            }}
          >
            <h2>{selectedNote.title || selectedNote.topic || "Untitled"}</h2>
            <p style={{ color: "#666", fontSize: 13 }}>
              🕒 {selectedNote.timestamp || "N/A"}
            </p>

            {selectedNote.response && (
              <>
                <h3>💬 AI Clarification</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>{selectedNote.response}</p>
              </>
            )}

            {selectedNote.summary && (
              <>
                <h3>📋 Summary</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>{selectedNote.summary}</p>
              </>
            )}

            {selectedNote.content && (
              <>
                <h3>📝 Content</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>{selectedNote.content}</p>
              </>
            )}

            {/* 🗓️ Planner Schedule View */}
            {Array.isArray(selectedNote.schedule) &&
              selectedNote.schedule.length > 0 && (
                <>
                  <h3>🗓️ Daily Schedule</h3>
                  {selectedNote.schedule.map((day, idx) => (
                    <div key={idx} style={{ marginBottom: 12 }}>
                      <h4 style={{ marginBottom: 6, color: "#2563eb" }}>
                        📅 {day.date}
                      </h4>
                      {Array.isArray(day.blocks) && day.blocks.length > 0 ? (
                        day.blocks.map((block, i) => (
                          <div
                            key={i}
                            style={{
                              background: "#f3f4f6",
                              padding: "8px 10px",
                              borderRadius: 8,
                              marginBottom: 5,
                            }}
                          >
                            <p style={{ margin: 0, fontWeight: 600 }}>
                              {block.task}
                            </p>
                            <p style={{ margin: "2px 0", fontSize: 13 }}>
                              ⏰ {block.start_time} - {block.end_time} |{" "}
                              {block.hours} hrs | Difficulty:{" "}
                              {block.difficulty}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p style={{ color: "#777" }}>
                          No tasks scheduled for this day.
                        </p>
                      )}
                    </div>
                  ))}
                </>
              )}

            <button
              onClick={() => setSelectedNote(null)}
              style={{
                marginTop: 15,
                backgroundColor: "#2563eb",
                color: "#fff",
                border: "none",
                padding: "10px 18px",
                borderRadius: 8,
                cursor: "pointer",
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
