import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Screens
import HomeScreen from "./screens/HomeScreen";
import AutoNoteScreen from "./screens/AutoNoteScreen";
import FocusScreen from "./screens/FocusScreen";
import PlannerScreen from "./screens/PlannerScreen";
import DoubtsScreen from "./screens/DoubtsScreen";
import FlashcardsScreen from "./screens/FlashcardsScreen";
import MoodScreen from "./screens/MoodScreen";
import DistractionScreen from "./screens/DistractionScreen";
import BrainDumpScreen from "./screens/BrainDumpScreen";
import ConfusionScreen from "./screens/ConfusionScreen";
import ChatbotScreen from "./screens/ChatbotScreen";
import SavedFolderScreen from "./screens/SavedFolderScreen";   // ✅ New import
import NotesListScreen from "./screens/NotesListScreen";       // ✅ Optional (if you want individual lists)

export default function App() {
  return (
    <Router>
      <Routes>
        {/* 🔹 Main Home Page */}
        <Route path="/" element={<HomeScreen />} />

        {/* 🔹 Saved Folder */}
        <Route path="/saved" element={<SavedFolderScreen />} />   {/* ✅ new route */}
        <Route path="/notes/:module" element={<NotesListScreen />} /> {/* ✅ if using module-wise notes */}

        {/* 🔹 Core Features */}
        <Route path="/autonote" element={<AutoNoteScreen />} />
        <Route path="/focus" element={<FocusScreen />} />
        <Route path="/planner" element={<PlannerScreen />} />
        <Route path="/doubts" element={<DoubtsScreen />} />
        <Route path="/flashcards" element={<FlashcardsScreen />} />
        <Route path="/mood" element={<MoodScreen />} />
        <Route path="/distraction" element={<DistractionScreen />} />
        <Route path="/braindump" element={<BrainDumpScreen />} />
        <Route path="/confusion" element={<ConfusionScreen />} />
        <Route path="/chatbot" element={<ChatbotScreen />} />
      </Routes>
    </Router>
  );
}
