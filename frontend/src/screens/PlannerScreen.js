// ---- PlannerScreen.jsx (FULL FIXED VERSION) ---- //

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { plannerGenerate, savePlanner } from "../api";

export default function PlannerScreen() {
  const navigate = useNavigate();

  // ------------------------------- Task Inputs
  const [task, setTask] = useState("");
  const [due, setDue] = useState("");
  const [time, setTime] = useState("");
  const [difficulty, setDifficulty] = useState(3);

  // ------------------------------- States
  const [tasks, setTasks] = useState([]);
  const [routine, setRoutine] = useState([]);

  const [activity, setActivity] = useState("");
  const [rStart, setRStart] = useState("");
  const [rEnd, setREnd] = useState("");

  const [plan, setPlan] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [summary, setSummary] = useState("");

  useEffect(() => {
    if ("Notification" in window) Notification.requestPermission();
  }, []);

  // ------------------------------- Add Task
  const addTask = () => {
    if (!task.trim() || !due.trim() || !time.trim()) {
      alert("Please enter task, date & time!");
      return;
    }

    // Correct ISO datetime with IST timezone
    const dueDateTime = `${due}T${time}:00+05:30`;

    setTasks((prev) => [
      ...prev,
      {
        name: task,
        subject: "General",
        due: dueDateTime,
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

  // ------------------------------- Add Routine Slot
  const addRoutine = () => {
    if (!activity.trim() || !rStart || !rEnd) {
      alert("Please enter activity & timings!");
      return;
    }

    setRoutine((prev) => [...prev, { label: activity, start: rStart, end: rEnd }]);

    setActivity("");
    setRStart("");
    setREnd("");
  };

  const deleteRoutine = (i) => setRoutine(routine.filter((_, idx) => idx !== i));

  // ------------------------------- Generate Plan
  const generatePlan = async () => {
    if (tasks.length === 0) return alert("Add at least one task!");

    setLoading(true);
    setPlan([]);

    try {
      const currentDateTimeIST = new Date()
        .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
        .replace(" ", "T");

      const payload = {
        tasks,
        routine,
        start_datetime: currentDateTimeIST,
        preferred_hours: 4,
        end_date: null,
      };

      const res = await plannerGenerate(payload);
      const data = res.data;

      if (data.schedule?.length > 0) {
        setPlan(data.schedule);
        setSummary(
          `Plan generated for ${data.schedule.length} days covering ${tasks.length} tasks.`
        );
      } else {
        alert("⚠️ Backend could not generate a plan.");
      }
    } catch (err) {
      console.error("Planner error:", err);
      alert("⚠️ Backend error while generating plan.");
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------- Save Plan
  const handleSavePlan = async () => {
    if (plan.length === 0) return alert("Nothing to save!");

    setSaving(true);
    try {
      await savePlanner(summary, plan, tasks, new Date().toISOString().split("T")[0]);
      alert("Saved!");
    } catch {
      alert("Save failed.");
    } finally {
      setSaving(false);
    }
  };

  // ------------------------------- Helpers
  const toFloatHour = (t) => {
    if (!t) return 0;
    const [h, m] = t.split(":").map(Number);
    return h + m / 60;
  };

  const getColor = (type, diff) => {
    if (type === "routine") return "rgba(102,153,255,0.4)";
    if (diff <= 2) return "#22c55e";
    if (diff === 3) return "#facc15";
    return "#ef4444";
  };

  // -------------------------------------------------------------- UI
  return (
    <div style={page}>
      <button onClick={() => navigate(-1)} style={backBtn}>← Back</button>

      <h2 style={heading}>📅 AURA Smart Planner</h2>

      {/* Routine Builder */}
      <div style={cardBox}>
        <h3>⏰ Your Daily Routine</h3>

        <input value={activity} onChange={(e) => setActivity(e.target.value)}
          placeholder="Activity (Breakfast)" style={inputStyle} />

        <input type="time" value={rStart}
          onChange={(e) => setRStart(e.target.value)} style={inputStyle} />

        <input type="time" value={rEnd}
          onChange={(e) => setREnd(e.target.value)} style={inputStyle} />

        <button onClick={addRoutine} style={addBtn}>➕ Add Routine Slot</button>

        {routine.map((r, i) => (
          <div key={i} style={routineCard}>
            <b>{r.label}</b> — {r.start} to {r.end}
            <button onClick={() => deleteRoutine(i)} style={deleteSmall}>✖</button>
          </div>
        ))}
      </div>

      {/* Task Builder */}
      <div style={cardBox}>
        <h3>🧾 Add a Task</h3>

        <input value={task} onChange={(e) => setTask(e.target.value)}
          placeholder="Task name" style={inputStyle} />

        <input type="date" value={due}
          onChange={(e) => setDue(e.target.value)} style={inputStyle} />

        <input type="time" value={time}
          onChange={(e) => setTime(e.target.value)} style={inputStyle} />

        <input type="number" min={1} max={5} value={difficulty}
          onChange={(e) => setDifficulty(Number(e.target.value))}
          style={inputStyle} />

        <button onClick={addTask} style={addBtn}>➕ Add Task</button>
      </div>

      {/* Task List */}
      {tasks.length > 0 && (
        <div style={cardBox}>
          <h3>🧾 Your Tasks</h3>
          {tasks.map((t, i) => (
            <div key={i} style={taskCard}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <b>{t.name}</b>
                <button onClick={() => deleteTask(i)} style={deleteSmall}>🗑</button>
              </div>
              <p style={{ margin: "4px 0", color: "#C7C9E0" }}>
                📅 {new Date(t.due).toLocaleString("en-IN")}
                | ⚙️ Difficulty: {t.difficulty}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={generatePlan}
        disabled={loading || tasks.length === 0}
        style={generateBtn}
      >
        {loading ? "Generating..." : "⚡ Generate Smart Study Plan"}
      </button>

      {summary && <div style={summaryBox}>{summary}</div>}

      {/* Timeline */}
      {plan.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <h3>🧠 24-Hour Smart Timetable</h3>

          <div style={timelineWrapper}>
            {plan.map((day, i) => (
              <div key={i} style={timelineColumn}>
                <div style={dateHeader}>
                  {new Date(day.date).toLocaleDateString("en-IN", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })}
                </div>

                <div style={timelineDayGrid}>
                  {/* Hour Marks */}
                  {Array.from({ length: 24 }).map((_, idx) => (
                    <div key={idx} style={hourLine}>
                      <span style={hourLabel}>{idx}:00</span>
                    </div>
                  ))}

                  {/* Routine Blocks */}
                  {routine.map((r, idx) => {
                    const start = toFloatHour(r.start);
                    const end = toFloatHour(r.end);
                    return (
                      <div key={`r${idx}`}
                        style={{
                          ...blockBase,
                          background: getColor("routine"),
                          top: start * 40,
                          height: Math.max((end - start) * 40, 15),
                        }}>
                        {r.label}
                      </div>
                    );
                  })}

                  {/* Task Blocks */}
                  {day.blocks.map((b, idx) => {
                    const start = toFloatHour(b.start_time);
                    const end = toFloatHour(b.end_time);
                    return (
                      <div key={`b${idx}`}
                        style={{
                          ...blockBase,
                          background: getColor("task", b.difficulty),
                          top: start * 40,
                          height: Math.max((end - start) * 40, 15),
                        }}>
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
            style={mainBtn}
          >
            {saving ? "Saving..." : "💾 Save Plan"}
          </button>
        </div>
      )}
    </div>
  );
}

/* --------------------------------------------------
   Styles (unchanged)
-------------------------------------------------- */

const page = {
  minHeight: "100vh",
  background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
  color: "#EAEAF5",
  fontFamily: "'Poppins', sans-serif",
  padding: 20,
};

const backBtn = {
  background: "none",
  border: "none",
  color: "#C7C9E0",
  fontSize: 16,
  marginBottom: 10,
  cursor: "pointer",
};

const heading = { fontSize: 28, fontWeight: "700" };

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

const generateBtn = {
  background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
  color: "white",
  padding: "12px",
  borderRadius: 8,
  border: "none",
  width: "100%",
  fontWeight: 600,
  cursor: "pointer",
  marginBottom: 20,
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
  marginTop: 20,
};

const routineCard = {
  background: "rgba(255,255,255,0.05)",
  padding: 10,
  borderRadius: 8,
  marginBottom: 8,
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
};

const deleteSmall = {
  background: "none",
  border: "none",
  cursor: "pointer",
  color: "#ef4444",
  fontSize: 18,
};

const summaryBox = {
  background: "rgba(255,255,255,0.1)",
  padding: 12,
  borderRadius: 10,
  color: "#A5B4FC",
  marginBottom: 20,
};

const timelineWrapper = {
  display: "flex",
  gap: 20,
  overflowX: "auto",
  paddingTop: 10,
};

const timelineColumn = {
  minWidth: 220,
  background: "rgba(255,255,255,0.08)",
  borderRadius: 10,
  padding: 10,
  position: "relative",
  boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
};

const timelineDayGrid = {
  position: "relative",
  height: 960,
  borderLeft: "2px solid rgba(255,255,255,0.2)",
};

const hourLine = {
  height: 40,
  borderBottom: "1px dashed rgba(255,255,255,0.1)",
  display: "flex",
  alignItems: "center",
  paddingLeft: 4,
};

const hourLabel = {
  fontSize: 10,
  color: "#ccc",
};

const dateHeader = {
  fontWeight: 600,
  marginBottom: 8,
  color: "#fff",
};

const taskCard = {
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.1)",
  padding: 12,
  borderRadius: 10,
  marginBottom: 10,
  boxShadow: "0 3px 8px rgba(0,0,0,0.3)",
};

const blockBase = {
  position: "absolute",
  left: "12%",
  width: "80%",
  borderRadius: 6,
  color: "#fff",
  textAlign: "center",
  fontSize: 12,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow: "0 4px 10px rgba(0,0,0,0.3)",
};
