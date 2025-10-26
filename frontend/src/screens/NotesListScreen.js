import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function NotesListScreen() {
  const { module } = useParams();
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState(null);

  const API_BASE = "http://127.0.0.1:8000";

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
      // ✅ Handle AutoNote separately — supports /autonote/notes/get/{id}
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

  // 🧹 Helper: capitalize module name
  const formatTitle = (text) =>
    text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();

  return (
    <div
      style={{
        backgroundColor: "#f9fafb",
        minHeight: "100vh",
        padding: 20,
      }}
    >
      {/* 🔙 Back Button */}
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

      {/* 🧾 Title */}
      <h2 style={{ fontSize: 28, fontWeight: "700", marginBottom: 20 }}>
        📘 {formatTitle(module)} Notes
      </h2>

      {/* 📄 Note List */}
      {loading ? (
        <p>Loading saved notes...</p>
      ) : entries.length === 0 ? (
        <p style={{ color: "#999" }}>No saved notes found.</p>
      ) : (
        entries.map((note) => (
          <div
            key={note.id}
            onClick={() => openNote(note.id)}
            style={{
              backgroundColor: "#fff",
              border: "1px solid #ddd",
              borderRadius: 10,
              padding: 15,
              marginBottom: 10,
              cursor: "pointer",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={(ev) =>
              (ev.currentTarget.style.backgroundColor = "#f3f4f6")
            }
            onMouseLeave={(ev) =>
              (ev.currentTarget.style.backgroundColor = "#fff")
            }
          >
            <p style={{ margin: 0, fontWeight: 600 }}>
              {note.title || "Untitled"}
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
              {note.content || note.summary || "[No content available]"}
            </p>
            <p style={{ fontSize: 12, color: "#888" }}>
              🕒 {note.timestamp || "N/A"}
            </p>
          </div>
        ))
      )}

      {/* 🪟 Modal Popup - Full Note Viewer */}
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
            {/* 🧾 Note Title */}
            <h2>{selectedNote.title || "Untitled Note"}</h2>
            <p style={{ color: "#666", fontSize: 13 }}>
              🕒 {selectedNote.timestamp || "N/A"}
            </p>

            {/* 📋 Summary */}
            {selectedNote.summary && (
              <>
                <h3>📋 Summary</h3>
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {selectedNote.summary}
                </p>
              </>
            )}

            {/* ⭐ Highlights */}
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

            {/* 🏷️ Keywords (for synopsis alignment) */}
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

            {/* 🔹 Bullets */}
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

            {/* 🗒️ Transcript */}
            {selectedNote.transcript && (
              <>
                <h3>🗒️ Transcript</h3>
                <p
                  style={{
                    background: "#f9fafb",
                    border: "1px solid #eee",
                    borderRadius: 8,
                    padding: 10,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {selectedNote.transcript}
                </p>
              </>
            )}

            {/* 🔘 Close Button */}
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
