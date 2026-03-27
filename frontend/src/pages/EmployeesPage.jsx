import React, { useEffect, useState } from "react";
import { listUsers, createUser, updateUser, deleteUser } from "../api/client";

const ROLES = ["Owner", "Manager", "Employee"];

function UserRow({ user, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(user.name);
  const [role, setRole] = useState(user.role);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSave() {
    setError("");
    try {
      const data = { name, role };
      if (password) data.password = password;
      await updateUser(user.id, data);
      setEditing(false);
      setPassword("");
      onUpdate();
    } catch (err) {
      setError(err.response?.data?.detail || "Update failed");
    }
  }

  return (
    <tr>
      {editing ? (
        <>
          <td>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </td>
          <td>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </td>
          <td>
            <input
              type="password"
              placeholder="New password (optional)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </td>
          <td>
            <button onClick={handleSave}>Save</button>
            <button onClick={() => { setEditing(false); setPassword(""); }}>Cancel</button>
            {error && <span className="error"> {error}</span>}
          </td>
        </>
      ) : (
        <>
          <td>{user.name}</td>
          <td>{user.role}</td>
          <td>—</td>
          <td>
            <button onClick={() => setEditing(true)}>Edit</button>
            <button
              className="btn-danger"
              onClick={() => { if (window.confirm(`Delete ${user.name}?`)) onDelete(user.id); }}
            >
              Delete
            </button>
          </td>
        </>
      )}
    </tr>
  );
}

export default function EmployeesPage() {
  const [users, setUsers] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState("Employee");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const res = await listUsers();
    setUsers(res.data);
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      await createUser({ name, role, password });
      setName("");
      setPassword("");
      setShowCreate(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create user");
    }
  }

  async function handleDelete(id) {
    await deleteUser(id);
    load();
  }

  return (
    <div className="employees-page">
      <h2>Employees / Users</h2>
      <table className="history-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Role</th>
            <th>Password</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <UserRow key={u.id} user={u} onUpdate={load} onDelete={handleDelete} />
          ))}
        </tbody>
      </table>

      <button onClick={() => setShowCreate(!showCreate)} style={{ marginTop: 16 }}>
        + New User
      </button>

      {showCreate && (
        <form className="inline-form" onSubmit={handleCreate} style={{ marginTop: 8 }}>
          <input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <input
            type="password"
            placeholder="Password (8+ chars)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Create</button>
          <button type="button" onClick={() => setShowCreate(false)}>Cancel</button>
          {error && <span className="error"> {error}</span>}
        </form>
      )}
    </div>
  );
}
