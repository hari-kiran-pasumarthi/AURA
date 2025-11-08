import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function NotesListScreen() {
  const { module } = useParams();
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState(null);

  const API_BASE = "https://loyal-beauty-production.up.railway.app/";

  // 🧠 Fetch saved notes for the selected module
  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const res = await fetch(`${API_BASE}/notes/list/${module}`);
        const data = await res.json();
        setEntries(Array.isArray(data.entries) ? data.entries : []);
      } catch (err) {
        console.error("⚠️ Failed to fetch notes:", err);
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };
    fetchNotes();
  }, [module]);

  // 🧩 Fetch individual note details
  const openNote = async (id) => {
    try {
      const endpoint =
        module === "autonote"
          ? `${API_BASE}/autonote/notes/get/${id}`
          : `${API_BASE}/notes/get/${module}/${id}`;

      const res = await fetch(endpoint);
      if (!res.ok) throw new Error("Failed to load note");
      const note = await res.json();
      setSelectedNote(note);
    } catch (err) {
      alert("⚠️ Could not open this note.");
      console.error(err);
    }
  };

  const formatTitle = (text) =>
    text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
        padding: 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* 🔹 Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          maxWidth: 900,
          background: "rgba(255,255,255,0.08)",
          borderRadius: 15,
          padding: "12px 20px",
          boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
          backdropFilter: "blur(10px)",
          marginBottom: 25,
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
          <h3 style={{ margin: 0, fontWeight: 700 }}>
            {formatTitle(module)} Notes
          </h3>
        </div>
      </div>

      {/* 📄 Notes List */}
      <div
        style={{
          width: "100%",
          maxWidth: 900,
          display: "flex",
          flexDirection: "column",
          gap: 15,
        }}
      >
        {loading ? (
          <p style={{ color: "#C7C9E0", textAlign: "center" }}>Loading saved notes...</p>
        ) : entries.length === 0 ? (
          <p style={{ color: "#C7C9E0", textAlign: "center" }}>
            No saved notes found.
          </p>
        ) : (
          entries.map((note) => (
            <div
              key={note.id}
              onClick={() => openNote(note.id)}
              style={{
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 15,
                padding: 18,
                cursor: "pointer",
                boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
                transition: "transform 0.25s ease, box-shadow 0.25s ease",
                backdropFilter: "blur(8px)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-5px)";
                e.currentTarget.style.boxShadow =
                  "0 6px 25px rgba(200,200,255,0.25)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow =
                  "0 4px 20px rgba(0,0,0,0.25)";
              }}
            >
              <h4
                style={{
                  margin: 0,
                  fontSize: 18,
                  fontWeight: 700,
                  color: "#EAEAF5",
                }}
              >
                {note.title || "Untitled"}
              </h4>
              <p
                style={{
                  color: "#C7C9E0",
                  margin: "5px 0",
                  fontSize: 14,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {note.content || note.summary || "[No content available]"}
              </p>
              <p style={{ fontSize: 12, color: "#A8B0D0" }}>
                🕒 {note.timestamp || "N/A"}
              </p>
            </div>
          ))
        )}
      </div>

      {/* 🪟 Note Viewer Modal */}
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
            animation: "fadeIn 0.3s ease",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "rgba(255,255,255,0.1)",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 15,
              padding: 25,
              width: "90%",
              maxWidth: 700,
              maxHeight: "80vh",
              overflowY: "auto",
              boxShadow: "0 8px 30px rgba(0,0,0,0.4)",
              backdropFilter: "blur(15px)",
              color: "#EAEAF5",
              animation: "slideIn 0.3s ease",
            }}
          >
            <h2 style={{ color: "#EAEAF5" }}>
              {selectedNote.title || "Untitled Note"}
            </h2>
            <p style={{ color: "#C7C9E0", fontSize: 13 }}>
              🕒 {selectedNote.timestamp || "N/A"}
            </p>

            {selectedNote.summary && (
              <>
                <h3>📋 Summary</h3>
                <p style={{ whiteSpace: "pre-wrap", color: "#EAEAF5" }}>
                  {selectedNote.summary}
                </p>
              </>
            )}

            {selectedNote.highlights?.length > 0 && (
              <>
                <h3>⭐ Highlights</h3>
                <ul>
                  {selectedNote.highlights.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </>
            )}

            {selectedNote.keywords?.length > 0 && (
              <>
                <h3>🏷️ Keywords</h3>
                <ul>
                  {selectedNote.keywords.map((k, i) => (
                    <li key={i}>{k}</li>
                  ))}
                </ul>
              </>
            )}

            {selectedNote.bullets?.length > 0 && (
              <>
                <h3>🔹 Key Points</h3>
                <ul>
                  {selectedNote.bullets.map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              </>
            )}

            {selectedNote.transcript && (
              <>
                <h3>🗒️ Transcript</h3>
                <p
                  style={{
                    background: "rgba(255,255,255,0.08)",
                    borderRadius: 8,
                    padding: 10,
                    color: "#EAEAF5",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {selectedNote.transcript}
                </p>
              </>
            )}

            <button
              onClick={() => setSelectedNote(null)}
              style={{
                marginTop: 15,
                background: "linear-gradient(135deg, #2563EB, #4F46E5)",
                color: "white",
                border: "none",
                padding: "10px 20px",
                borderRadius: 10,
                cursor: "pointer",
                fontWeight: 600,
                boxShadow: "0 4px 15px rgba(59,130,246,0.3)",
              }}
            >
              Close
            </button>
          </div>

          {/* ✨ Animations */}
          <style>
            {`
              @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
              }
              @keyframes slideIn {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
              }
            `}
          </style>
        </div>
      )}
    </div>
  );
}
