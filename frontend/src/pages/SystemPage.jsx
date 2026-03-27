import React, { useEffect, useState } from "react";
import { getEspStatus, getDemoMode, setDemoMode, processPending } from "../api/client";

export default function SystemPage() {
  const [espStatus, setEspStatus] = useState(null);
  const [demo, setDemo] = useState(false);
  const [pendingResult, setPendingResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    try {
      const [esp, dm] = await Promise.all([getEspStatus(), getDemoMode()]);
      setEspStatus(esp.data);
      setDemo(dm.data.enabled);
    } catch {}
  }

  useEffect(() => { load(); }, []);

  async function handleToggleDemo() {
    await setDemoMode(!demo);
    load();
  }

  async function handleProcessPending() {
    setLoading(true);
    try {
      const res = await processPending();
      setPendingResult(res.data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="system-page">
      <h2>System</h2>

      <section>
        <h3>ESP32 Status</h3>
        {espStatus ? (
          <dl>
            <dt>Reachable</dt>
            <dd style={{ color: espStatus.reachable ? "#4caf50" : "#f44336" }}>
              {espStatus.reachable ? "✅ Yes" : "❌ No"}
            </dd>
            <dt>Status</dt>
            <dd>{espStatus.status || "—"}</dd>
            <dt>Demo Mode</dt>
            <dd>{espStatus.demo_mode ? "Enabled" : "Disabled"}</dd>
          </dl>
        ) : (
          <p>Loading…</p>
        )}
        <button onClick={load}>Refresh</button>
      </section>

      <section>
        <h3>Demo Mode</h3>
        <p>
          When enabled, relay commands are simulated without contacting the ESP32.
        </p>
        <button onClick={handleToggleDemo}>
          {demo ? "Disable Demo Mode" : "Enable Demo Mode"}
        </button>
      </section>

      <section>
        <h3>Pending Relay Actions</h3>
        <p>
          Retry queued relay commands that failed while ESP32 was unreachable.
        </p>
        <button onClick={handleProcessPending} disabled={loading}>
          {loading ? "Processing…" : "Process Pending"}
        </button>
        {pendingResult && (
          <p>
            Processed: {pendingResult.processed} | Failed: {pendingResult.failed}
          </p>
        )}
      </section>
    </div>
  );
}
