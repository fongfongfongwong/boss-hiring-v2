import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchDashboardStats,
  fetchTasks,
  fetchFunnel,
  pauseTask,
  resumeTask,
  stopTask,
  type DashboardStats,
  type TaskSummary,
  type FunnelStage,
} from "../api/client";
import { useTaskWebSocket, type WSEvent } from "../hooks/useWebSocket";
import { statusLabel, statusColor } from "../lib/utils";
import {
  Users,
  FileCheck,
  UserCheck,
  Phone,
  Play,
  Pause,
  Square,
  Activity,
} from "lucide-react";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [activeFunnel, setActiveFunnel] = useState<FunnelStage[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<number | null>(null);
  const { events } = useTaskWebSocket(activeTaskId);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10_000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [s, t] = await Promise.all([fetchDashboardStats(), fetchTasks()]);
      setStats(s);
      setTasks(t);

      const running = t.find((t) => t.status === "running");
      if (running) {
        setActiveTaskId(running.id);
        const f = await fetchFunnel(running.id);
        setActiveFunnel(f.funnel);
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function handlePause(id: number) {
    await pauseTask(id);
    loadData();
  }
  async function handleResume(id: number) {
    await resumeTask(id);
    loadData();
  }
  async function handleStop(id: number) {
    await stopTask(id);
    loadData();
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">招聘看板</h1>
        <Link
          to="/tasks/new"
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          + 新建招聘任务
        </Link>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            icon={<Users className="text-blue-500" />}
            label="候选人总数"
            value={stats.total_candidates}
          />
          <StatCard
            icon={<FileCheck className="text-indigo-500" />}
            label="已收简历"
            value={stats.resume_received}
          />
          <StatCard
            icon={<UserCheck className="text-green-500" />}
            label="评分达标"
            value={stats.qualified}
          />
          <StatCard
            icon={<Phone className="text-emerald-500" />}
            label="已获联系方式"
            value={stats.contact_obtained}
          />
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Funnel */}
        <div className="col-span-2 bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">招聘漏斗</h2>
          {activeFunnel.length > 0 ? (
            <div className="space-y-3">
              {activeFunnel.map((stage, i) => {
                const maxCount = activeFunnel[0]?.count || 1;
                const width = Math.max((stage.count / maxCount) * 100, 8);
                return (
                  <div key={stage.stage} className="flex items-center gap-3">
                    <span className="w-28 text-sm text-gray-600 text-right">
                      {stage.stage}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-8 overflow-hidden">
                      <div
                        className="h-full rounded-full flex items-center px-3 text-white text-sm font-medium transition-all duration-500"
                        style={{
                          width: `${width}%`,
                          backgroundColor: `hsl(${220 - i * 25}, 70%, ${50 + i * 3}%)`,
                        }}
                      >
                        {stage.count}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">
              暂无运行中的任务
            </p>
          )}
        </div>

        {/* Live Log */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity size={18} className="text-green-500" />
            实时日志
          </h2>
          <div className="h-72 overflow-y-auto space-y-1.5 text-xs font-mono">
            {events.length === 0 ? (
              <p className="text-gray-400 text-center py-8">等待任务启动...</p>
            ) : (
              events
                .slice()
                .reverse()
                .map((evt, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-gray-400 shrink-0">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-gray-700">{evt.message}</span>
                  </div>
                ))
            )}
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="bg-white rounded-xl shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">任务列表</h2>
        </div>
        {tasks.length === 0 ? (
          <p className="text-gray-400 text-center py-8">暂无任务</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-left">
              <tr>
                <th className="px-6 py-3 font-medium">ID</th>
                <th className="px-6 py-3 font-medium">职位</th>
                <th className="px-6 py-3 font-medium">状态</th>
                <th className="px-6 py-3 font-medium">进度</th>
                <th className="px-6 py-3 font-medium">创建时间</th>
                <th className="px-6 py-3 font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {tasks.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 font-mono text-gray-500">
                    #{t.id}
                  </td>
                  <td className="px-6 py-3 font-medium">{t.position_title}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor(
                        t.status
                      )}`}
                    >
                      {statusLabel(t.status)}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-gray-500">
                    {t.progress.greeted ?? 0} 招呼 / {t.progress.resume_received ?? 0} 简历
                  </td>
                  <td className="px-6 py-3 text-gray-500">
                    {t.created_at
                      ? new Date(t.created_at).toLocaleString("zh-CN")
                      : ""}
                  </td>
                  <td className="px-6 py-3">
                    <div className="flex gap-1.5">
                      {t.status === "running" && (
                        <>
                          <button
                            onClick={() => handlePause(t.id)}
                            className="p-1.5 rounded hover:bg-yellow-50 text-yellow-600"
                            title="暂停"
                          >
                            <Pause size={16} />
                          </button>
                          <button
                            onClick={() => handleStop(t.id)}
                            className="p-1.5 rounded hover:bg-red-50 text-red-600"
                            title="停止"
                          >
                            <Square size={16} />
                          </button>
                        </>
                      )}
                      {t.status === "paused" && (
                        <button
                          onClick={() => handleResume(t.id)}
                          className="p-1.5 rounded hover:bg-green-50 text-green-600"
                          title="继续"
                        >
                          <Play size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-5 flex items-center gap-4">
      <div className="p-3 rounded-lg bg-gray-50">{icon}</div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}
