import React, { useEffect, useState } from "react";
import { getHistory } from "../api/client";

function formatDate(ts) {
  if (!ts) return "-";
  return new Date(ts * 1000).toLocaleString();
}

function formatDuration(secs) {
  if (!secs) return "0m";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m`;
}

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chFilter, setChFilter] = useState("");
  const [limit, setLimit] = useState(50);

  async function load() {
    setLoading(true);
    try {
      const params = { limit };
      if (chFilter) params.ch = Number(chFilter);
      const res = await getHistory(params);
      setHistory(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [chFilter, limit]);

  return (
    <div className="history-page">
      <h2>Session History</h2>
      <div className="filters">
        <label>
          Table:&nbsp;
          <input
            type="number"
            placeholder="All"
            value={chFilter}
            onChange={(e) => setChFilter(e.target.value)}
            min={1}
            style={{ width: 60 }}
          />
        </label>
        <label>
          Show:&nbsp;
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>
        <button onClick={load}>Refresh</button>
      </div>

      {loading ? (
        <p>Loading…</p>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Table</th>
              <th>Customer</th>
              <th>Mode</th>
              <th>Started</th>
              <th>Ended</th>
              <th>Duration</th>
              <th>Cost</th>
              <th>Actor</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr><td colSpan={8} style={{ textAlign: "center" }}>No records</td></tr>
            ) : (
              history.map((row) => (
                <tr key={row.id}>
                  <td>Table {row.ch}</td>
                  <td>{row.customer}</td>
                  <td>{row.mode}</td>
                  <td>{formatDate(row.started_at)}</td>
                  <td>{formatDate(row.ended_at)}</td>
                  <td>{formatDuration(row.duration_s)}</td>
                  <td>{row.total_cost > 0 ? `$${row.total_cost.toFixed(2)}` : "-"}</td>
                  <td>{row.actor || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
