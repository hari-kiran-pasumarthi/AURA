import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// 🧩 Utils
import ProtectedRoute from "./utils/ProtectedRoute"; // ✅ import guard

// 🏠 Core Screens
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
import SavedFolderScreen from "./screens/SavedFolderScreen";
import NotesListScreen from "./screens/NotesListScreen";

// 🔐 Auth Screens
import LoginScreen from "./screens/LoginScreen";
import SignupScreen from "./screens/SignupScreen";

export default function App() {
  return (
    <Router>
      <Routes>
        {/* 🔹 Auth routes (unprotected) */}
        <Route path="/" element={<LoginScreen />} />
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/signup" element={<SignupScreen />} />

        {/* 🔹 Protected Routes */}
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <HomeScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/autonote"
          element={
            <ProtectedRoute>
              <AutoNoteScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/focus"
          element={
            <ProtectedRoute>
              <FocusScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/planner"
          element={
            <ProtectedRoute>
              <PlannerScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/doubts"
          element={
            <ProtectedRoute>
              <DoubtsScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/flashcards"
          element={
            <ProtectedRoute>
              <FlashcardsScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/mood"
          element={
            <ProtectedRoute>
              <MoodScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/distraction"
          element={
            <ProtectedRoute>
              <DistractionScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/braindump"
          element={
            <ProtectedRoute>
              <BrainDumpScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/confusion"
          element={
            <ProtectedRoute>
              <ConfusionScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/chatbot"
          element={
            <ProtectedRoute>
              <ChatbotScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/saved"
          element={
            <ProtectedRoute>
              <SavedFolderScreen />
            </ProtectedRoute>
          }
        />

        <Route
          path="/notes/:module"
          element={
            <ProtectedRoute>
              <NotesListScreen />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}
