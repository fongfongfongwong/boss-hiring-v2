import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchPositions, type PositionSummary } from "../api/client";
import { Briefcase, Users } from "lucide-react";

export default function PositionList() {
  const [positions, setPositions] = useState<PositionSummary[]>([]);

  useEffect(() => {
    fetchPositions().then(setPositions);
  }, []);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">职位管理</h1>
        <Link
          to="/tasks/new"
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          + 新建职位
        </Link>
      </div>

      {positions.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <Briefcase size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-400">暂无职位，点击上方按钮创建</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {positions.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{p.title}</h3>
                  {p.description && (
                    <p className="text-sm text-gray-500 mt-1">{p.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  <Users size={14} />
                  {p.candidate_count}
                </div>
              </div>
              <div className="mt-3 text-xs text-gray-400">
                创建于{" "}
                {p.created_at
                  ? new Date(p.created_at).toLocaleDateString("zh-CN")
                  : "未知"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
