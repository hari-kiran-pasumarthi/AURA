import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { plannerGenerate, savePlanner } from "../api"; // centralized axios API

export default function PlannerScreen() {
  const navigate = useNavigate();
  const [task, setTask] = useState("");
  const [due, setDue] = useState("");
  const [time, setTime] = useState(""); // ⏰ time input
  const [difficulty, setDifficulty] = useState(3);
  const [tasks, setTasks] = useState([]);
  const [plan, setPlan] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [summary, setSummary] = useState("");

  useEffect(() => {
    if ("Notification" in window) Notification.requestPermission();
  }, []);

  const addTask = () => {
    if (!task.trim() || !due.trim() || !time.trim())
      return alert("Please enter task name, date, and time!");

    const dueDateTime = `${due}T${time}`;
    setTasks([
      ...tasks,
      {
        name: task,
        subject: "General",
        due: dueDateTime,          // full datetime string
        difficulty,
        estimated_hours: difficulty * 1.5,
        completed: false,
      },
    ]);
    setTask("");
    setDue("");
    setTime("");
    setDifficulty(3);
  };

  const deleteTask = (i) => setTasks(tasks.filter((_, idx) => idx !== i));
  const toggleCompletion = (i) => {
    const updated = [...tasks];
    updated[i].completed = !updated[i].completed;
    setTasks(updated);
  };

  // ✅ Generate AI Plan with Option B behaviour
  const generatePlan = async () => {
    if (tasks.length === 0) return alert("Please add at least one task!");
    setLoading(true);
    setPlan([]);

    try {
      // ⏰ Send full current datetime (not just date)
      const currentDateTimeISO = new Date().toISOString();

      const res = await plannerGenerate(
        tasks,
        currentDateTimeISO, // <-- start_datetime for backend
        null,
        4
      );

      const data = res.data;
      if (data.schedule?.length) {
        setPlan(data.schedule);
        setSummary(
          `✅ Plan generated for ${data.schedule.length} days covering ${tasks.length} tasks.`
        );
        alert("✨ Smart Study Plan Generated!");
      } else {
        alert("⚠️ Failed to generate plan. Please try again.");
      }
    } catch (err) {
      if (err.response?.status === 401) {
        alert("⚠️ Session expired. Please log in again.");
        localStorage.removeItem("token");
        window.location.href = "/login";
      } else {
        alert("⚠️ Could not connect to backend.");
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  // ✅ Save Plan
  const handleSavePlan = async () => {
    if (plan.length === 0) return alert("No plan to save!");
    setSaving(true);
    try {
      await savePlanner(
        summary,
        plan,
        tasks,
        new Date().toISOString().split("T")[0]
      );
      alert("💾 Plan saved successfully!");
    } catch (err) {
      if (err.response?.status === 401) {
        alert("⚠️ Session expired. Please log in again.");
        localStorage.removeItem("token");
        window.location.href = "/login";
      } else {
        alert("⚠️ Failed to save plan.");
        console.error(err);
      }
    } finally {
      setSaving(false);
    }
  };

  // 🔔 Notifications
  useEffect(() => {
    if (plan.length === 0) return;
    plan.forEach((day) => {
      day.blocks.forEach((b) => {
        if (!b.start_time || b.start_time === "N/A") return;
        const [h, m] = b.start_time.split(":").map(Number);
        const sessionTime = new Date(`${day.date}T${h}:${m}:00`);
        const notifyTime = sessionTime.getTime() - 1 * 60 * 1000;
        const now = Date.now();
        if (notifyTime > now) {
          setTimeout(() => {
            if (Notification.permission === "granted") {
              new Notification("⏰ Study Reminder", {
                body: `${b.task} starts at ${b.start_time}`,
              });
            }
          }, notifyTime - now);
        }
      });
    });
  }, [plan]);

  const progress =
    tasks.length === 0
      ? 0
      : (tasks.filter((t) => t.completed).length / tasks.length) * 100;

  const toFloatHour = (t) => {
    if (t === "N/A") return 7;
    const [h, m] = t.split(":").map(Number);
    return h + m / 60;
  };

  const getColor = (diff) => {
    if (diff <= 2) return "#22c55e";
    if (diff === 3) return "#facc15";
    return "#ef4444";
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
        padding: 20,
      }}
    >
      <button
        onClick={() => navigate(-1)}
        style={{
          background: "none",
          border: "none",
          color: "#C7C9E0",
          fontSize: 16,
          marginBottom: 10,
          cursor: "pointer",
        }}
      >
        ← Back
      </button>

      <h2 style={{ fontSize: 28, fontWeight: "700" }}>📅 AURA Smart Planner</h2>
      <p style={{ color: "#BFC2D5", marginBottom: 10 }}>
        Organize, track and let AI plan your study sessions.
      </p>

      {/* 📊 Progress bar */}
      <div
        style={{
          background: "rgba(255,255,255,0.15)",
          height: 10,
          borderRadius: 6,
          overflow: "hidden",
          marginBottom: 15,
        }}
      >
        <div
          style={{
            width: `${progress}%`,
            height: "100%",
            background: "#22c55e",
            transition: "width 0.3s",
          }}
        />
      </div>

      {/* 🧠 Task Inputs */}
      <div style={cardBox}>
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Enter task name"
          style={inputStyle}
        />
        <input
          type="date"
          value={due}
          onChange={(e) => setDue(e.target.value)}
          style={inputStyle}
        />
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          style={inputStyle}
        />
        <input
          type="number"
          min={1}
          max={5}
          value={difficulty}
          onChange={(e) => setDifficulty(Number(e.target.value))}
          placeholder="Difficulty (1–5)"
          style={inputStyle}
        />
        <button onClick={addTask} style={addBtn}>
          ➕ Add Task
        </button>
        <button onClick={generatePlan} disabled={loading} style={mainBtn}>
          {loading ? "⏳ Generating..." : "⚡ Generate AI Plan"}
        </button>
      </div>

      {/* 📝 Task List */}
      {tasks.length > 0 && (
        <div style={cardBox}>
          <h3>🧾 Your Tasks</h3>
          {tasks.map((t, i) => (
            <div key={i} style={taskCard}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <b>{t.name}</b>
                <button
                  onClick={() => deleteTask(i)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#ef4444",
                    cursor: "pointer",
                    fontSize: 18,
                  }}
                >
                  🗑
                </button>
              </div>
              <p style={{ margin: "4px 0", color: "#C7C9E0" }}>
                📅 {new Date(t.due).toLocaleString()} | ⚙️ Difficulty:{" "}
                {t.difficulty}
              </p>
              <label style={{ fontSize: 14 }}>
                <input
                  type="checkbox"
                  checked={t.completed}
                  onChange={() => toggleCompletion(i)}
                />{" "}
                Mark as completed
              </label>
            </div>
          ))}
        </div>
      )}

      {summary && (
        <div
          style={{
            background: "rgba(255,255,255,0.1)",
            borderRadius: 10,
            padding: 12,
            marginBottom: 20,
            color: "#A5B4FC",
          }}
        >
          {summary}
        </div>
      )}

      {/* 🧩 Timeline */}
      {plan.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <h3>🧠 Study Timeline</h3>
          <div style={timelineWrapper}>
            {plan.map((day, i) => (
              <div key={i} style={timelineColumn}>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>
                  {new Date(day.date).toLocaleDateString(undefined, {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })}
                </div>
                <div style={timelineDayGrid}>
                  {Array.from({ length: 15 }).map((_, idx) => (
                    <div key={idx} style={hourLine}>
                      <span style={{ fontSize: 10 }}>{7 + idx}:00</span>
                    </div>
                  ))}
                  {day.blocks.map((b, idx) => {
                    const start = toFloatHour(b.start_time);
                    const end = toFloatHour(b.end_time);
                    const top = (start - 7) * 40;
                    const height = (end - start) * 40;
                    return (
                      <div
                        key={idx}
                        style={{
                          position: "absolute",
                          top,
                          left: "10%",
                          width: "80%",
                          height,
                          background: getColor(b.difficulty),
                          borderRadius: 6,
                          color: "#fff",
                          fontSize: 13,
                          textAlign: "center",
                          lineHeight: `${height}px`,
                          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
                        }}
                        title={`${b.task} (${b.start_time}–${b.end_time})`}
                      >
                        {b.task}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleSavePlan}
            disabled={saving}
            style={{ ...mainBtn, marginTop: 25 }}
          >
            {saving ? "Saving..." : "💾 Save Plan"}
          </button>
        </div>
      )}
    </div>
  );
}

/* 💅 Styles */
const cardBox = {
  background: "rgba(255,255,255,0.08)",
  borderRadius: 15,
  padding: 20,
  marginBottom: 20,
  backdropFilter: "blur(8px)",
  boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
};
const inputStyle = {
  width: "100%",
  padding: 10,
  borderRadius: 8,
  border: "1px solid rgba(255,255,255,0.2)",
  background: "rgba(255,255,255,0.1)",
  color: "#EAEAF5",
  marginBottom: 10,
};
const addBtn = {
  background: "linear-gradient(135deg, #22c55e, #16a34a)",
  color: "white",
  padding: "10px",
  borderRadius: 8,
  border: "none",
  width: "100%",
  marginBottom: 10,
  cursor: "pointer",
};
const mainBtn = {
  background: "linear-gradient(135deg, #2563EB, #4F46E5)",
  color: "white",
  padding: "12px",
  borderRadius: 8,
  border: "none",
  width: "100%",
  fontWeight: 600,
  cursor: "pointer",
};
const taskCard = {
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.1)",
  padding: 12,
  borderRadius: 10,
  marginBottom: 10,
  boxShadow: "0 3px 8px rgba(0,0,0,0.3)",
};
const timelineWrapper = {
  display: "flex",
  gap: 20,
  overflowX: "auto",
  padding: "10px 0",
};
const timelineColumn = {
  minWidth: 180,
  position: "relative",
  background: "rgba(255,255,255,0.08)",
  borderRadius: 10,
  padding: 10,
  boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
  border: "1px solid rgba(255,255,255,0.1)",
};
const timelineDayGrid = {
  position: "relative",
  height: 600,
  borderLeft: "2px solid rgba(255,255,255,0.2)",
};
const hourLine = {
  height: 40,
  borderBottom: "1px dashed rgba(255,255,255,0.1)",
  position: "relative",
  paddingLeft: 4,
};
