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

  // ⚙️ Upload & Generate Flashcards
  const generateFlashcards = async () => {
    if (!text.trim() && !file) {
      alert("⚠️ Please enter text or upload a PDF before generating.");
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

        const uploadRes = await fetch(
          "https://loyal-beauty-production.up.railway.app/flashcards/upload-pdf/",
          { method: "POST", body: formData }
        );

        if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);
        const uploadData = await uploadRes.json();
        payload.pdf_path = uploadData.pdf_path;
      } else {
        payload.text = text;
      }

      const res = await fetch(
        "https://loyal-beauty-production.up.railway.app/flashcards/generate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

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
          cards,
        },
      };

      const res = await fetch(
        "https://loyal-beauty-production.up.railway.app/flashcards/save",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) throw new Error(`Save failed: ${res.status}`);
      const data = await res.json();
      alert(`✅ Flashcards saved successfully as ${data.filename}`);
    } catch (err) {
      console.error("❌ Save failed:", err);
      alert("⚠️ Could not save flashcards. Try again.");
    }
  };

  // Card Navigation
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
          width: "100%",
          maxWidth: 800,
          background: "rgba(255, 255, 255, 0.08)",
          backdropFilter: "blur(10px)",
          borderRadius: 15,
          padding: "12px 20px",
          boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
          marginBottom: 30,
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
            marginRight: 15,
          }}
        >
          ← Back
        </button>
        <img
          src="/FullLogo.jpg"
          alt="AURA Logo"
          style={{
            width: 45,
            height: 45,
            borderRadius: 10,
            marginRight: 12,
            boxShadow: "0 0 15px rgba(182,202,255,0.3)",
          }}
        />
        <h2 style={{ margin: 0, fontWeight: 700 }}>Smart Flashcard Generator</h2>
      </div>

      {/* 🧾 Input Section */}
      <div
        style={{
          background: "rgba(255,255,255,0.08)",
          padding: 20,
          borderRadius: 20,
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
          width: "100%",
          maxWidth: 600,
          marginBottom: 20,
        }}
      >
        <input
          placeholder="Enter Topic (optional)"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          style={inputStyle}
        />
        <textarea
          placeholder="Paste your notes or text..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          style={{ ...inputStyle, resize: "vertical" }}
        />

        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
          style={{ marginBottom: 10, color: "#EAEAF5" }}
        />

        <button
          onClick={generateFlashcards}
          disabled={loading}
          style={{
            ...buttonStyle,
            background: loading
              ? "rgba(147,197,253,0.3)"
              : "linear-gradient(135deg, #2563EB, #4F46E5)",
          }}
        >
          {loading ? "⏳ Generating..." : "⚡ Generate Flashcards"}
        </button>
      </div>

      {/* 🧠 Flashcard Display */}
      {cards.length > 0 && (
        <>
          <div
            onClick={() => setFlipped(!flipped)}
            style={{
              width: 320,
              height: 220,
              perspective: "1000px",
              cursor: "pointer",
              marginTop: 20,
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

          <p style={{ marginTop: 10, color: "#C7C9E0" }}>
            {index + 1} / {cards.length} (Click card to flip)
          </p>

          <button
            onClick={handleSave}
            style={{
              ...navBtn,
              background: "linear-gradient(135deg, #10B981, #34D399)",
              marginTop: 10,
            }}
          >
            💾 Save Flashcards
          </button>
        </>
      )}

      {/* ✨ Animations */}
      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>
    </div>
  );
}

// 💅 Styles
const inputStyle = {
  width: "100%",
  background: "rgba(255,255,255,0.1)",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 12,
  padding: 12,
  fontSize: 16,
  color: "#EAEAF5",
  marginBottom: 10,
  outline: "none",
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
  marginTop: 10,
  cursor: "pointer",
  boxShadow: "0 4px 20px rgba(59,130,246,0.3)",
};

const frontCard = {
  position: "absolute",
  width: "100%",
  height: "100%",
  backfaceVisibility: "hidden",
  background: "rgba(255,255,255,0.1)",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 15,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  textAlign: "center",
  fontSize: 18,
  fontWeight: "600",
  color: "#EAEAF5",
  boxShadow: "0 6px 25px rgba(0,0,0,0.3)",
  backdropFilter: "blur(10px)",
  padding: 10,
};

const backCard = {
  ...frontCard,
  background: "linear-gradient(135deg, #2563EB, #4F46E5)",
  transform: "rotateY(180deg)",
};

const navBtn = {
  background: "linear-gradient(135deg, #2563EB, #4F46E5)",
  color: "white",
  fontWeight: "600",
  border: "none",
  borderRadius: 10,
  padding: "10px 20px",
  cursor: "pointer",
  transition: "transform 0.25s ease",
};
