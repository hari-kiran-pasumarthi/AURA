import React from "react";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";

const AudioToText = ({ onResult }) => {
  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  if (!SpeechRecognition.browserSupportsSpeechRecognition()) {
    return <p>❌ Your browser doesn’t support speech recognition.</p>;
  }

  const startListening = () => {
    resetTranscript();
    SpeechRecognition.startListening({ continuous: true, language: "en-IN" });
  };

  const stopListening = () => {
    SpeechRecognition.stopListening();
    if (onResult) onResult(transcript);
  };

  return (
    <div style={{ textAlign: "center", margin: "20px" }}>
      <button
        onClick={listening ? stopListening : startListening}
        style={{
          backgroundColor: listening ? "#FF3B30" : "#007AFF",
          color: "white",
          padding: "10px 20px",
          borderRadius: "10px",
          border: "none",
          cursor: "pointer",
          fontSize: "16px",
        }}
      >
        {listening ? "Stop Recording" : "🎙️ Start Speaking"}
      </button>

      <p style={{ marginTop: "10px" }}>
        {listening ? "Listening..." : "Tap to start recording"}
      </p>

      <textarea
        value={transcript}
        readOnly
        rows="5"
        style={{ width: "100%", marginTop: "10px", padding: "10px", fontSize: "16px" }}
      />
    </div>
  );
};

export default AudioToText;
