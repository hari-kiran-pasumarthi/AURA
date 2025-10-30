import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function PlannerScreen() {
  const navigate = useNavigate();
  const [task, setTask] = useState("");
  const [due, setDue] = useState("");
  const [difficulty, setDifficulty] = useState(3);
  const [tasks, setTasks] = useState([]);
  const [plan, setPlan] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [summary, setSummary] = useState("");

  useEffect(() => {
    if ("Notification" in window) Notification.requestPermission();
  }, []);

  // 🔹 Auto-load saved Smart Calendar on mount
  useEffect(() => {
    const loadSavedCalendar = async () => {
      try {
        const res = await fetch("https://loyal-beauty-production.up.railway.app/planner/calendar/list");
        if (!res.ok) throw new Error("Failed to load saved calendar");
        const data = await res.json();
        if (data.entries && data.entries.length > 0) {
          // Group entries by date
          const grouped = {};
          data.entries.forEach((e) => {
            if (!grouped[e.date]) grouped[e.date] = [];
            grouped[e.date].push({
              task: e.task,
              subject: e.subject,
              hours: e.hours,
              start_time: e.start_time || "N/A",
              end_time: e.end_time || "N/A",
              difficulty: e.difficulty || 3,
              due: e.due || "",
            });
          });
          const formattedPlan = Object.entries(grouped).map(([date, blocks]) => ({
            date,
            blocks,
          }));
          setPlan(formattedPlan);
          setSummary(`📅 Loaded ${formattedPlan.length} saved study days from Smart Calendar`);
        }
      } catch (err) {
        console.warn("⚠️ Could not load saved calendar:", err);
      }
    };

    loadSavedCalendar();
  }, []); // runs once when the screen opens

  const addTask = () => {
    if (!task.trim() || !due.trim()) return alert("Please enter task & due date!");
    setTasks([
      ...tasks,
      {
        name: task,
        subject: "General",
        due,
        difficulty,
        estimated_hours: difficulty * 1.5,
        completed: false,
      },
    ]);
    setTask("");
    setDue("");
    setDifficulty(3);
  };

  const deleteTask = (i) => setTasks(tasks.filter((_, idx) => idx !== i));
  const toggleCompletion = (i) => {
    const updated = [...tasks];
    updated[i].completed = !updated[i].completed;
    setTasks(updated);
  };

  const generatePlan = async () => {
    if (tasks.length === 0) return alert("Please add at least one task!");
    setLoading(true);
    setPlan([]);

    const body = {
      tasks,
      start_date: new Date().toISOString().split("T")[0],
      daily_hours: 4,
    };

    try {
      const res = await fetch("https://loyal-beauty-production.up.railway.app/planner/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data = await res.json();

      if (data.schedule?.length > 0) {
        setPlan(data.schedule);
        setSummary(
          `✅ Plan generated for ${data.schedule.length} study days covering ${tasks.length} tasks.`
        );
        alert("Smart Study Plan Generated!");
      } else alert("⚠️ No schedule generated. Adjust your tasks or dates.");
    } catch (err) {
      console.error("❌ Planner generation failed:", err);
      alert("⚠️ Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const savePlan = async () => {
    if (plan.length === 0) return alert("No plan to save!");
    setSaving(true);
    try {
      const res = await fetch("https://loyal-beauty-production.up.railway.app/planner/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary, schedule: plan, tasks }),
      });
      if (!res.ok) throw new Error("Save failed");
      alert("💾 Plan saved successfully!");
    } catch (e) {
      console.error("⚠️ Save failed:", e);
      alert("⚠️ Failed to save plan. Check backend connection.");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    if (plan.length === 0) return;
    plan.forEach((day) => {
      day.blocks.forEach((b) => {
        if (!b.start_time || b.start_time === "N/A") return;
        const [h, m] = b.start_time.split(":").map(Number);
        const sessionTime = new Date(`${day.date}T${h.toString().padStart(2, "0")}:${m}:00`);
        const reminderTime = sessionTime.getTime() - 10 * 60 * 1000;
        const now = Date.now();
        if (reminderTime > now) {
          setTimeout(() => {
            if (Notification.permission === "granted") {
              new Notification("⏰ Study Reminder", {
                body: `${b.task} starts at ${b.start_time}`,
              });
            }
          }, reminderTime - now);
        }
      });
    });
  }, [plan]);

  const completedCount = tasks.filter((t) => t.completed).length;
  const progress = tasks.length === 0 ? 0 : (completedCount / tasks.length) * 100;

  const toFloatHour = (t) => {
    if (t === "N/A") return 7;
    const [h, m] = t.split(":").map(Number);
    return h + m / 60;
  };

  const getColor = (diff) => {
    if (diff <= 2) return "#16a34a";
    if (diff === 3) return "#f59e0b";
    return "#dc2626";
  };

  return (
    <div style={{ padding: 20, backgroundColor: "#f9fafb", minHeight: "100vh" }}>
      <button
        onClick={() => navigate(-1)}
        style={{ background: "none", border: "none", color: "#2563eb", fontSize: 16 }}
      >
        ← Back
      </button>

      <h2 style={{ fontSize: 28, fontWeight: "700", marginBottom: 10 }}>📅 AI Auto Planner</h2>
      <p style={{ color: "#555" }}>Visualize and recall your smart study plans anytime.</p>

      <div style={{ backgroundColor: "#e5e7eb", height: 10, borderRadius: 5, overflow: "hidden" }}>
        <div
          style={{
            width: `${progress}%`,
            height: "100%",
            backgroundColor: "#16a34a",
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <p style={{ color: "#555", marginBottom: 15 }}>
        {completedCount}/{tasks.length} tasks completed
      </p>

      {/* Input section */}
      <input value={task} onChange={(e) => setTask(e.target.value)} placeholder="Enter task name" style={inputStyle} />
      <input value={due} onChange={(e) => setDue(e.target.value)} placeholder="Due date (YYYY-MM-DD)" style={inputStyle} />
      <input type="number" min={1} max={5} value={difficulty} onChange={(e) => setDifficulty(Number(e.target.value))} placeholder="Difficulty (1–5)" style={inputStyle} />
      <button onClick={addTask} style={addBtn}>➕ Add Task</button>
      <button onClick={generatePlan} disabled={loading} style={mainBtn}>
        {loading ? "⏳ Generating..." : "⚡ Generate Plan"}
      </button>

      {tasks.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h3>📝 Your Tasks</h3>
          {tasks.map((t, i) => (
            <div key={i} style={taskCard}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <b>{t.name}</b>
                <button onClick={() => deleteTask(i)} style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer" }}>🗑</button>
              </div>
              <p style={{ margin: "5px 0", color: "#555" }}>📅 {t.due} | ⚙️ Difficulty: {t.difficulty}</p>
              <label style={{ fontSize: 14 }}>
                <input type="checkbox" checked={t.completed} onChange={() => toggleCompletion(i)} /> Mark as completed
              </label>
            </div>
          ))}
        </div>
      )}

      {summary && <div style={summaryBox}>📊 <b>Planner Summary:</b> {summary}</div>}

      {plan.length > 0 && (
        <div style={{ marginTop: 30 }}>
          <h3 style={{ fontSize: 22, fontWeight: "700" }}>🧠 Study Timeline (7 AM – 10 PM)</h3>
          <div style={timelineWrapper}>
            {plan.map((day, i) => (
              <div key={i} style={timelineColumn}>
                <div style={{ fontWeight: 600, marginBottom: 8 }}>
                  {new Date(day.date).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
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
                        title={`${b.task} (${b.start_time}–${b.end_time})`}
                        style={{
                          position: "absolute",
                          top,
                          left: "10%",
                          width: "80%",
                          height,
                          background: getColor(b.difficulty),
                          borderRadius: 6,
                          color: "white",
                          fontSize: 13,
                          textAlign: "center",
                          lineHeight: `${height}px`,
                          boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
                        }}
                      >
                        {b.task}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <button onClick={savePlan} disabled={saving} style={{ ...mainBtn, marginTop: 25, backgroundColor: saving ? "#93c5fd" : "#2563eb" }}>
            {saving ? "Saving..." : "💾 Save Plan"}
          </button>
        </div>
      )}
    </div>
  );
}

const inputStyle = { width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ddd", marginBottom: 10 };
const addBtn = { background: "#22c55e", color: "white", padding: "10px", borderRadius: 8, border: "none", width: "100%", marginBottom: 10 };
const mainBtn = { background: "#2563eb", color: "white", padding: "12px", borderRadius: 8, border: "none", width: "100%", fontWeight: 600 };
const taskCard = { background: "#fff", padding: 12, borderRadius: 10, border: "1px solid #ddd", marginBottom: 10 };
const summaryBox = { background: "#eef2ff", border: "1px solid #c7d2fe", borderRadius: 10, padding: 12, marginTop: 20, color: "#1e3a8a" };
const timelineWrapper = { display: "flex", gap: 20, overflowX: "auto", padding: "10px 0" };
const timelineColumn = { minWidth: 180, position: "relative", background: "#fff", borderRadius: 10, border: "1px solid #ddd", padding: 10, boxShadow: "0 2px 6px rgba(0,0,0,0.05)" };
const timelineDayGrid = { position: "relative", height: 600, borderLeft: "2px solid #ddd" };
const hourLine = { height: 40, borderBottom: "1px dashed #ddd", position: "relative", paddingLeft: 4 };
