import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchCandidates,
  type CandidateSummary,
} from "../api/client";
import { statusLabel, statusColor } from "../lib/utils";
import { Search, Download, ChevronLeft, ChevronRight } from "lucide-react";

export default function CandidateList() {
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const pageSize = 20;

  useEffect(() => {
    loadCandidates();
  }, [page, statusFilter]);

  async function loadCandidates() {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    if (statusFilter) params.set("status", statusFilter);
    params.set("sort_by", "created_at");
    params.set("order", "desc");

    const data = await fetchCandidates(params.toString());
    setCandidates(data.items);
    setTotal(data.total);
  }

  const totalPages = Math.ceil(total / pageSize);

  const statuses = [
    "", "found", "greeted", "chatting", "resume_received",
    "scored", "qualified", "contact_obtained", "rejected",
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">候选人管理</h1>
        <a
          href="/api/candidates/export"
          className="flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
        >
          <Download size={16} /> 导出 Excel
        </a>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border rounded-lg text-sm bg-white"
        >
          <option value="">全部状态</option>
          {statuses
            .filter(Boolean)
            .map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-left">
            <tr>
              <th className="px-6 py-3 font-medium">姓名</th>
              <th className="px-6 py-3 font-medium">状态</th>
              <th className="px-6 py-3 font-medium">初筛分数</th>
              <th className="px-6 py-3 font-medium">简历评分</th>
              <th className="px-6 py-3 font-medium">联系方式</th>
              <th className="px-6 py-3 font-medium">创建时间</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {candidates.map((c) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-6 py-3">
                  <Link
                    to={`/candidates/${c.id}`}
                    className="text-primary-600 hover:underline font-medium"
                  >
                    {c.name || `#${c.id}`}
                  </Link>
                </td>
                <td className="px-6 py-3">
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor(
                      c.status
                    )}`}
                  >
                    {statusLabel(c.status)}
                  </span>
                </td>
                <td className="px-6 py-3 font-mono">
                  {c.pre_match_score > 0 ? c.pre_match_score : "-"}
                </td>
                <td className="px-6 py-3 font-mono">
                  {c.resume_score != null ? (
                    <span
                      className={
                        c.is_qualified ? "text-green-600 font-semibold" : ""
                      }
                    >
                      {c.resume_score}
                    </span>
                  ) : (
                    "-"
                  )}
                </td>
                <td className="px-6 py-3">
                  {c.has_contact ? (
                    <span className="text-green-600 text-xs font-medium">
                      已获取
                    </span>
                  ) : (
                    <span className="text-gray-400 text-xs">-</span>
                  )}
                </td>
                <td className="px-6 py-3 text-gray-500 text-xs">
                  {c.created_at
                    ? new Date(c.created_at).toLocaleString("zh-CN")
                    : ""}
                </td>
              </tr>
            ))}
            {candidates.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                  暂无候选人数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            共 {total} 条，第 {page}/{totalPages} 页
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
