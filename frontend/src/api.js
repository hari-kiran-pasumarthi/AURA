// frontend/utils/api.js
import axios from "axios";

// ✅ Configure your FastAPI backend base URL
const API = axios.create({
  baseURL:
    process.env.NEXT_PUBLIC_API_URL ||
    "https://loyal-beauty-production.up.railway.app",
});

// 🧩 Automatically attach Authorization token to every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 🧠 Handle expired or invalid tokens globally
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      alert("⚠️ Session expired or unauthorized. Please log in again.");
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// -------------------------------------------------------------
// 📚 AUTHENTICATION
// -------------------------------------------------------------

export const register = (name, email, password) =>
  API.post("/auth/signup", { name, email, password });

export const login = async (email, password) => {
  const res = await API.post("/auth/login", { email, password });
  if (res.data?.access_token) {
    localStorage.setItem("token", res.data.access_token);
  }
  return res.data;
};

export const logout = () => {
  localStorage.removeItem("token");
  window.location.href = "/login";
};

// -------------------------------------------------------------
// 📝 AUTONOTE – Transcription & Summarization
// -------------------------------------------------------------
export const autoNote = (text) => API.post("/autonote/transcribe", { text });

export const uploadAutoNote = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/autonote/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const summarizeAudio = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/autonote/audio", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getSavedAutoNotes = () => API.get("/autonote/saved");

// -------------------------------------------------------------
// 🧭 FOCUS – Focus Techniques & Tracking
// -------------------------------------------------------------
export const focus = (duration) => API.post("/focus/suggest", { duration });
export const getSavedFocus = () => API.get("/focus/saved");

// -------------------------------------------------------------
// 📅 PLANNER – Smart Study Planner
// -------------------------------------------------------------
export const plannerGenerate = (tasks, start_date, end_date, daily_hours = 4) =>
  API.post("/planner/generate", {
    start_date,
    end_date,
    daily_hours,
    tasks,
  });

export const savePlanner = (summary, schedule, tasks, date) =>
  API.post("/planner/save", { summary, schedule, tasks, date });

export const getSavedPlanner = () => API.get("/planner/saved");

// -------------------------------------------------------------
// ❓ DOUBTS – Question Handling
// -------------------------------------------------------------
export const doubts = (question) => API.post("/doubts/report", { question });
export const getDoubtHistory = () => API.get("/doubts/history");

// -------------------------------------------------------------
// 🎴 FLASHCARDS – AI Flashcard Generator
// -------------------------------------------------------------
export const flashcards = (topic) => API.post("/flashcards/generate", { topic });
export const getSavedFlashcards = () => API.get("/flashcards/saved");

// -------------------------------------------------------------
// 😊 MOOD TRACKER
// -------------------------------------------------------------
export const mood = (mood, intensity = 5, notes = "") =>
  API.post("/mood/log", { mood, intensity, notes });

export const getMoodLogs = () => API.get("/mood/logs");

// -------------------------------------------------------------
// 🕒 TIME PREDICTION
// -------------------------------------------------------------
export const timePredict = (topic, difficulty, pages) =>
  API.post("/timepredict/predict", { topic, difficulty, pages });

export const getSavedTimePredictions = () => API.get("/timepredict/saved");

// -------------------------------------------------------------
// 💭 BRAIN DUMP
// -------------------------------------------------------------
export const brainDump = (text) => API.post("/braindump/save", { text });
export const getSavedBrainDumps = () => API.get("/braindump/saved");

// -------------------------------------------------------------
// 😵 CONFUSION ANALYZER
// -------------------------------------------------------------
export const confusion = (question) =>
  API.post("/confusion/analyze", { text: question });

export const getSavedConfusion = () => API.get("/confusion/saved");

// -------------------------------------------------------------
// 🤖 CHATBOT – General Study Assistant
// -------------------------------------------------------------
export const chatbot = (query) => API.post("/chatbot/", { query });

export default API;
