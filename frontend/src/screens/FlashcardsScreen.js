import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function FlashcardsScreen() {
  const navigate = useNavigate();

  const [topic, setTopic] = useState("");
  const [text, setText] = useState("");
  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);

  const currentCard = cards[index];

  // ⚙️ Upload & Generate
  const generateFlashcards = async () => {
    if (!text.trim() && !file) {
      alert("Please enter text or upload a PDF before generating.");
      return;
    }

    setLoading(true);
    setCards([]);
    setFlipped(false);

    try {
      let payload = { pdf_path: null, text: "", num: 10 };

      if (file) {
        const formData = new FormData();
        formData.append("file", file);

        const uploadRes = await fetch("https://loyal-beauty-production.up.railway.app/flashcards/upload-pdf/", {
          method: "POST",
          body: formData,
        });

        if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);
        const uploadData = await uploadRes.json();

        payload.pdf_path = uploadData.pdf_path;
      } else {
        payload.text = text;
      }

      const res = await fetch("https://loyal-beauty-production.up.railway.app/flashcards/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Backend Error: ${res.status}`);
      const data = await res.json();
      setCards(data.cards || []);

      alert(`✅ Generated ${data.cards?.length || 0} flashcards!`);
    } catch (err) {
      console.error("❌ Flashcard generation failed:", err);
      alert("⚠️ Could not connect to backend. Ensure FastAPI is running.");
    } finally {
      setLoading(false);
    }
  };

  // 💾 Save Flashcards
  const handleSave = async () => {
    if (cards.length === 0) {
      alert("⚠️ No flashcards to save.");
      return;
    }

    try {
      const payload = {
        title: topic || "Manual Flashcards",
        content: `${cards.length} flashcards saved.`,
        metadata: {
          source: topic || "Manual Text Input",
          num_cards: cards.length,
          tags: ["manual"],
          cards: cards,
        },
      };

      const res = await fetch("https://loyal-beauty-production.up.railway.app/flashcards/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Save failed: ${res.status}`);
      const data = await res.json();
      alert(`✅ Flashcards saved successfully as ${data.filename}`);
    } catch (err) {
      console.error("❌ Save failed:", err);
      alert("⚠️ Could not save flashcards. Try again.");
    }
  };

  // Navigation
  const nextCard = () => {
    if (index < cards.length - 1) {
      setIndex(index + 1);
      setFlipped(false);
    }
  };
  const prevCard = () => {
    if (index > 0) {
      setIndex(index - 1);
      setFlipped(false);
    }
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
      }}
    >
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
        🧠 Smart Flashcard Generator
      </h2>

      <p style={{ color: "#555", textAlign: "center", marginBottom: 15 }}>
        Enter topic content or upload a study PDF to automatically generate flashcards.
      </p>

      <input
        placeholder="Enter Topic (optional)"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        style={inputStyle}
      />
      <textarea
        placeholder="Paste your notes or textbook text..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={6}
        style={{ ...inputStyle, resize: "vertical" }}
      />

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files[0])}
        style={{ marginBottom: 10 }}
      />

      <button
        onClick={generateFlashcards}
        disabled={loading}
        style={{
          ...buttonStyle,
          backgroundColor: loading ? "#93c5fd" : "#2563eb",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "⏳ Generating..." : "⚡ Generate Flashcards"}
      </button>

      {/* Flashcard Display */}
      {cards.length > 0 && (
        <>
          <div
            onClick={() => setFlipped(!flipped)}
            style={{
              width: 320,
              height: 220,
              perspective: "1000px",
              cursor: "pointer",
              marginTop: 30,
            }}
          >
            <div
              style={{
                width: "100%",
                height: "100%",
                position: "relative",
                transformStyle: "preserve-3d",
                transition: "transform 0.6s",
                transform: `rotateY(${flipped ? 180 : 0}deg)`,
              }}
            >
              <div style={frontCard}>
                <strong>Q:</strong> {currentCard?.q || "No Question"}
              </div>
              <div style={backCard}>
                <strong>A:</strong> {currentCard?.a || "No Answer"}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: 20, marginTop: 30 }}>
            <button onClick={prevCard} style={navBtn}>
              ◀ Prev
            </button>
            <button onClick={nextCard} style={navBtn}>
              Next ▶
            </button>
          </div>

          <p style={{ marginTop: 10 }}>
            {index + 1} / {cards.length}
          </p>
          <p style={{ color: "#888" }}>(Click card to flip)</p>

          <button
            onClick={handleSave}
            style={{
              ...navBtn,
              backgroundColor: "#10b981",
              marginTop: 10,
            }}
          >
            💾 Save Flashcards
          </button>
        </>
      )}
    </div>
  );
}

// 💅 Styles
const inputStyle = {
  width: "100%",
  maxWidth: 420,
  backgroundColor: "#fff",
  border: "1px solid #ddd",
  borderRadius: 10,
  padding: 12,
  fontSize: 16,
  marginBottom: 10,
};

const buttonStyle = {
  color: "white",
  fontSize: 18,
  fontWeight: "600",
  border: "none",
  borderRadius: 10,
  padding: "12px 18px",
  width: "100%",
  maxWidth: 420,
  marginBottom: 20,
};

const frontCard = {
  position: "absolute",
  width: "100%",
  height: "100%",
  backfaceVisibility: "hidden",
  backgroundColor: "#fff",
  border: "1px solid #ddd",
  borderRadius: 15,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  textAlign: "center",
  fontSize: 18,
  fontWeight: "600",
  color: "#111",
  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  padding: 10,
};

const backCard = {
  ...frontCard,
  backgroundColor: "#2563eb",
  color: "#fff",
  transform: "rotateY(180deg)",
};

const navBtn = {
  backgroundColor: "#2563eb",
  color: "white",
  fontWeight: "600",
  border: "none",
  borderRadius: 10,
  padding: "10px 20px",
  cursor: "pointer",
};
