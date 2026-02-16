import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CreateTask from "./pages/CreateTask";
import CandidateList from "./pages/CandidateList";
import CandidateDetail from "./pages/CandidateDetail";
import PositionList from "./pages/PositionList";
import MarketResearch from "./pages/MarketResearch";
import Settings from "./pages/Settings";
import {
  LayoutDashboard,
  PlusCircle,
  Users,
  Briefcase,
  Globe,
  Settings as SettingsIcon,
} from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "招聘看板" },
  { to: "/tasks/new", icon: PlusCircle, label: "新建任务" },
  { to: "/candidates", icon: Users, label: "候选人" },
  { to: "/positions", icon: Briefcase, label: "职位管理" },
  { to: "/market", icon: Globe, label: "市场调研" },
  { to: "/settings", icon: SettingsIcon, label: "设置" },
];

export default function App() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-60 bg-gray-900 text-gray-100 flex flex-col">
        <div className="px-6 py-5 border-b border-gray-800">
          <h1 className="text-lg font-bold tracking-tight">Boss 自动招聘</h1>
          <p className="text-xs text-gray-400 mt-1">Powered by RPA + AI</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-600 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-6 py-4 border-t border-gray-800 text-xs text-gray-500">
          v1.0.0
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks/new" element={<CreateTask />} />
          <Route path="/candidates" element={<CandidateList />} />
          <Route path="/candidates/:id" element={<CandidateDetail />} />
          <Route path="/positions" element={<PositionList />} />
          <Route path="/market" element={<MarketResearch />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
