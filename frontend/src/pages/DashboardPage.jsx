import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  listTables,
  startTimer,
  openTable,
  addTime,
  finishTable,
  outageAdjust,
  listQueue,
  addToQueue,
  removeFromQueue,
  assignQueue,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

function formatSeconds(secs) {
  if (!secs) return "0:00";
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function TableCard({ table, onAction }) {
  const { user } = useAuth();
  const [showStart, setShowStart] = useState(false);
  const [showOpen, setShowOpen] = useState(false);
  const [showAddTime, setShowAddTime] = useState(false);
  const [showOutage, setShowOutage] = useState(false);
  const [minutes, setMinutes] = useState(60);
  const [customer, setCustomer] = useState("");
  const [rate, setRate] = useState(20);
  const actor = user?.name || "";

  const statusColor = {
    idle: "#4caf50",
    active: "#2196f3",
    open: "#ff9800",
  }[table.status] || "#888";

  async function handleStart(e) {
    e.preventDefault();
    await startTimer(table.ch, { minutes: Number(minutes), customer, actor });
    setShowStart(false);
    setCustomer("");
    onAction();
  }

  async function handleOpen(e) {
    e.preventDefault();
    await openTable(table.ch, { customer, rate: Number(rate), actor });
    setShowOpen(false);
    setCustomer("");
    onAction();
  }

  async function handleAddTime(e) {
    e.preventDefault();
    await addTime(table.ch, { minutes: Number(minutes), actor });
    setShowAddTime(false);
    onAction();
  }

  async function handleFinish() {
    if (!window.confirm(`Finish table ${table.ch}?`)) return;
    await finishTable(table.ch, { actor });
    onAction();
  }

  async function handleOutage(e) {
    e.preventDefault();
    await outageAdjust(table.ch, { minutes: Number(minutes), actor });
    setShowOutage(false);
    onAction();
  }

  return (
    <div className="table-card" style={{ borderTop: `4px solid ${statusColor}` }}>
      <div className="table-header">
        <span className="table-num">Table {table.ch}</span>
        <span className="table-status" style={{ color: statusColor }}>
          {table.status.toUpperCase()}
        </span>
      </div>

      {table.status !== "idle" && (
        <div className="table-info">
          <div><strong>Customer:</strong> {table.customer}</div>
          {table.status === "active" && (
            <div><strong>Remaining:</strong> {formatSeconds(table.remaining_seconds)}</div>
          )}
          {table.status === "open" && (
            <>
              <div><strong>Elapsed:</strong> {formatSeconds(table.elapsed_seconds)}</div>
              <div><strong>Running cost:</strong> ${table.running_cost?.toFixed(2)}</div>
            </>
          )}
        </div>
      )}

      <div className="table-actions">
        {table.status === "idle" && (
          <>
            <button onClick={() => { setShowStart(!showStart); setShowOpen(false); }}>
              ⏱ Timed
            </button>
            <button onClick={() => { setShowOpen(!showOpen); setShowStart(false); }}>
              🔓 Open
            </button>
          </>
        )}
        {table.status === "active" && (
          <>
            <button onClick={() => { setShowAddTime(!showAddTime); setShowOutage(false); }}>
              ➕ Add Time
            </button>
            <button onClick={() => { setShowOutage(!showOutage); setShowAddTime(false); }}>
              ⚡ Outage
            </button>
            <button className="btn-danger" onClick={handleFinish}>
              ✅ Finish
            </button>
          </>
        )}
        {table.status === "open" && (
          <button className="btn-danger" onClick={handleFinish}>
            ✅ Finish &amp; Bill
          </button>
        )}
      </div>

      {showStart && (
        <form className="inline-form" onSubmit={handleStart}>
          <input
            placeholder="Customer name"
            value={customer}
            onChange={(e) => setCustomer(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Minutes"
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            min={1}
            required
          />
          <button type="submit">Start</button>
        </form>
      )}

      {showOpen && (
        <form className="inline-form" onSubmit={handleOpen}>
          <input
            placeholder="Customer name"
            value={customer}
            onChange={(e) => setCustomer(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Rate / hr"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            min={0}
            step="0.5"
            required
          />
          <button type="submit">Open</button>
        </form>
      )}

      {showAddTime && (
        <form className="inline-form" onSubmit={handleAddTime}>
          <input
            type="number"
            placeholder="Minutes to add"
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            min={1}
            required
          />
          <button type="submit">Add</button>
        </form>
      )}

      {showOutage && (
        <form className="inline-form" onSubmit={handleOutage}>
          <input
            type="number"
            placeholder="Outage minutes"
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            min={1}
            required
          />
          <button type="submit">Compensate</button>
        </form>
      )}
    </div>
  );
}

function QueuePanel({ queue, onAction }) {
  const { user } = useAuth();
  const [showAdd, setShowAdd] = useState(false);
  const [customer, setCustomer] = useState("");
  const [mode, setMode] = useState("timed");
  const [minutes, setMinutes] = useState(60);
  const [assignId, setAssignId] = useState(null);
  const [assignCh, setAssignCh] = useState(1);
  const actor = user?.name || "";

  async function handleAdd(e) {
    e.preventDefault();
    await addToQueue({ customer, mode, minutes: Number(minutes) });
    setCustomer("");
    setShowAdd(false);
    onAction();
  }

  async function handleRemove(id) {
    await removeFromQueue(id);
    onAction();
  }

  async function handleAssign(e) {
    e.preventDefault();
    await assignQueue({ queue_id: assignId, table_ch: Number(assignCh), actor });
    setAssignId(null);
    onAction();
  }

  return (
    <div className="queue-panel">
      <h3>Queue ({queue.length})</h3>
      {queue.map((entry) => (
        <div key={entry.id} className="queue-entry">
          <span>{entry.customer} — {entry.mode} {entry.mode === "timed" ? `${entry.minutes}min` : ""}</span>
          <div>
            <button onClick={() => setAssignId(entry.id)}>Assign</button>
            <button className="btn-danger" onClick={() => handleRemove(entry.id)}>✕</button>
          </div>
        </div>
      ))}

      {assignId && (
        <form className="inline-form" onSubmit={handleAssign}>
          <span>Table:</span>
          <input
            type="number"
            value={assignCh}
            onChange={(e) => setAssignCh(e.target.value)}
            min={1}
          />
          <button type="submit">Confirm</button>
          <button type="button" onClick={() => setAssignId(null)}>Cancel</button>
        </form>
      )}

      <button onClick={() => setShowAdd(!showAdd)}>+ Add to Queue</button>
      {showAdd && (
        <form className="inline-form" onSubmit={handleAdd}>
          <input
            placeholder="Customer"
            value={customer}
            onChange={(e) => setCustomer(e.target.value)}
            required
          />
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="timed">Timed</option>
            <option value="open">Open</option>
          </select>
          {mode === "timed" && (
            <input
              type="number"
              placeholder="Minutes"
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
              min={1}
            />
          )}
          <button type="submit">Add</button>
        </form>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const [tables, setTables] = useState([]);
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const [t, q] = await Promise.all([listTables(), listQueue()]);
      setTables(t.data);
      setQueue(q.data);
      setError(null);
    } catch (err) {
      setError("Failed to load data");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div className="dashboard">
      {error && <div className="error">{error}</div>}
      <div className="tables-grid">
        {tables.map((table) => (
          <TableCard key={table.ch} table={table} onAction={load} />
        ))}
      </div>
      <QueuePanel queue={queue} onAction={load} />
    </div>
  );
}
