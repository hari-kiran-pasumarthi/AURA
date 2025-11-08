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

// ✅ AutoNote – Speech-to-text or note transcription
export const autoNote = (text) => API.post("/autonote/transcribe", { text });

// ✅ Focus – Suggests focus techniques based on duration
export const focus = (duration) => API.post("/focus/suggest", { duration });

// ✅ Planner – Auto generates a study or task plan
export const planner = (task, due_date) =>
  API.post("/planner/generate", { task, due_date });

// ✅ Doubts – Submits a doubt or question
export const doubts = (question) => API.post("/doubts/report", { question });

// ✅ Flashcards – Creates study flashcards for a topic
export const flashcards = (topic) => API.post("/flashcards/generate", { topic });

// ✅ Mood – Logs mood and note
export const mood = (mood, intensity = 5, notes = "") =>
  API.post("/mood/log", { mood, intensity, notes });

// ✅ Distraction – Tracks distractions and suggests improvements
export const distraction = (duration) =>
  API.post("/distraction/track", { duration });

// ✅ Time Prediction – Predicts time needed for topic completion
export const timePredict = (topic, difficulty, pages) =>
  API.post("/timepredict/predict", { topic, difficulty, pages });

// ✅ Brain Dump – Organizes thoughts & saves them to file
export const brainDump = (text) => API.post("/braindump/save", { text });

// ✅ Confusion – Analyzes confusion and provides clarity tips
export const confusion = (question) =>
  API.post("/confusion/analyze", { text: question });

// ✅ Chatbot – General study assistant Q&A
export const chatbot = (query) => API.post("/chatbot/", { query });

export default API;
