import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

export default function LoginScreen() {
  const API_BASE = "https://loyal-beauty-production.up.railway.app";
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");

      localStorage.setItem("token", data.access_token);
      alert("✅ Welcome back!");
      navigate("/home");
    } catch (err) {
      alert(`⚠️ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(circle at 20% 20%, #2B3A55, #0B1020 80%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#EAEAF5",
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      <img
        src="/FullLogo.jpg"
        alt="AURA Logo"
        style={{
          width: 180,
          marginBottom: 20,
          borderRadius: 20,
          boxShadow: "0 0 20px rgba(182, 202, 255, 0.3)",
        }}
      />
      <h2 style={{ marginBottom: 10 }}>🔐 Login to AURA</h2>
      <p style={{ color: "#C7C9E0", marginBottom: 30 }}>
        Your adaptive AI study companion awaits ✨
      </p>

      <form
        onSubmit={handleLogin}
        style={{
          width: "90%",
          maxWidth: 350,
          background: "rgba(255,255,255,0.08)",
          padding: 25,
          borderRadius: 20,
          backdropFilter: "blur(8px)",
          boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
        }}
      >
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={inputStyle}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={inputStyle}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            ...btnStyle,
            background: loading ? "#93C5FD" : "#6C63FF",
          }}
        >
          {loading ? "⏳ Logging in..." : "🚀 Login"}
        </button>

        <p style={{ textAlign: "center", marginTop: 20, color: "#C7C9E0" }}>
          Don’t have an account?{" "}
          <Link to="/signup" style={{ color: "#93C5FD", textDecoration: "none" }}>
            Sign up
          </Link>
        </p>
      </form>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "10px",
  marginBottom: "15px",
  borderRadius: "10px",
  border: "1px solid rgba(255,255,255,0.2)",
  background: "rgba(255,255,255,0.1)",
  color: "#EAEAF5",
  fontSize: "16px",
};

const btnStyle = {
  width: "100%",
  padding: "12px",
  borderRadius: "10px",
  border: "none",
  color: "white",
  fontWeight: 600,
  cursor: "pointer",
};
