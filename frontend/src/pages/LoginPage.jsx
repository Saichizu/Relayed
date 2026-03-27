import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login, loading, error } = useAuth();
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError("");
    try {
      await login(password);
    } catch (err) {
      setLocalError(err.message);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>🎱 Relayed</h1>
        <h2>Pool Table Control</h2>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoFocus
            />
          </div>
          {(localError || error) && (
            <div className="error">{localError || error}</div>
          )}
          <button type="submit" disabled={loading || !password}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
