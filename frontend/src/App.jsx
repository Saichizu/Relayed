import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import EmployeesPage from "./pages/EmployeesPage";
import SystemPage from "./pages/SystemPage";
import "./App.css";

function Nav() {
  const { user, logout } = useAuth();
  return (
    <nav className="navbar">
      <span className="nav-brand">🎱 Relayed</span>
      <div className="nav-links">
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/history">History</NavLink>
        {user?.role !== "Employee" && <NavLink to="/employees">Employees</NavLink>}
        {user?.role === "Owner" && <NavLink to="/system">System</NavLink>}
      </div>
      <div className="nav-right">
        <span className="nav-user">{user?.name} ({user?.role})</span>
        <button className="nav-logout" onClick={logout}>Logout</button>
      </div>
    </nav>
  );
}

function AppRoutes() {
  const { user } = useAuth();
  if (!user) {
    return <LoginPage />;
  }
  return (
    <>
      <Nav />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/employees" element={<EmployeesPage />} />
          <Route path="/system" element={<SystemPage />} />
        </Routes>
      </main>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
