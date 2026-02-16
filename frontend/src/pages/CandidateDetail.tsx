import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchCandidate, fetchCandidateMessages } from "../api/client";
import { statusLabel, statusColor } from "../lib/utils";
import {
  ArrowLeft,
  User,
  FileText,
  MessageSquare,
  Phone,
  Mail,
  MessageCircle,
} from "lucide-react";

export default function CandidateDetail() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState<Record<string, any> | null>(null);
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    if (id) {
      fetchCandidate(Number(id)).then(setCandidate);
      fetchCandidateMessages(Number(id)).then(setMessages);
    }
  }, [id]);

  if (!candidate) {
    return (
      <div className="p-6 text-gray-400 text-center">加载中...</div>
    );
  }

  const resume = candidate.resume as Record<string, any> | undefined;
  const contact = candidate.contact as Record<string, any> | undefined;
  const score = resume?.score || {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <Link
        to="/candidates"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft size={16} /> 返回列表
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border p-6 flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center">
            <User className="text-primary-600" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold">{candidate.name || `候选人 #${id}`}</h1>
            <span
              className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${statusColor(
                candidate.status
              )}`}
            >
              {statusLabel(candidate.status)}
            </span>
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          <p>初筛分数: <strong>{candidate.pre_match_score}</strong></p>
          {resume && (
            <p>
              简历评分:{" "}
              <strong className={resume.is_qualified ? "text-green-600" : ""}>
                {resume.weighted_total}
              </strong>
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left: Resume & Score */}
        <div className="col-span-2 space-y-6">
          {/* Score Radar Placeholder */}
          {resume && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FileText size={18} /> AI 评分详情
              </h2>
              <div className="grid grid-cols-5 gap-4 mb-4">
                {[
                  { label: "技能匹配", value: score.skill_match },
                  { label: "经验相关", value: score.experience_relevance },
                  { label: "学历契合", value: score.education_fit },
                  { label: "项目质量", value: score.project_quality },
                  { label: "综合推荐", value: score.overall_recommendation },
                ].map((dim) => (
                  <div key={dim.label} className="text-center">
                    <div className="relative w-16 h-16 mx-auto mb-2">
                      <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                        <circle
                          cx="18"
                          cy="18"
                          r="14"
                          fill="none"
                          stroke="#e5e7eb"
                          strokeWidth="3"
                        />
                        <circle
                          cx="18"
                          cy="18"
                          r="14"
                          fill="none"
                          stroke={dim.value >= 70 ? "#22c55e" : dim.value >= 50 ? "#f59e0b" : "#ef4444"}
                          strokeWidth="3"
                          strokeDasharray={`${(dim.value / 100) * 88} 88`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">
                        {dim.value}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">{dim.label}</p>
                  </div>
                ))}
              </div>

              {score.strengths && (
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-green-700 mb-1">亮点</h4>
                  <ul className="text-sm text-gray-600 list-disc ml-5">
                    {score.strengths.map((s: string, i: number) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {score.weaknesses && (
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-red-700 mb-1">不足</h4>
                  <ul className="text-sm text-gray-600 list-disc ml-5">
                    {score.weaknesses.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {score.reasoning && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">评分理由</h4>
                  <p className="text-sm text-gray-600">{score.reasoning}</p>
                </div>
              )}
            </div>
          )}

          {/* Resume download */}
          {resume?.file_path && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-3">简历文件</h2>
              <a
                href={`/api/candidates/${id}/resume`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-lg text-sm font-medium hover:bg-primary-100"
              >
                <FileText size={16} /> 下载简历 ({resume.file_type})
              </a>
            </div>
          )}
        </div>

        {/* Right: Chat & Contact */}
        <div className="space-y-6">
          {/* Contact Info */}
          {contact && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Phone size={18} /> 联系方式
              </h2>
              <div className="space-y-2 text-sm">
                {contact.wechat && (
                  <div className="flex items-center gap-2">
                    <MessageCircle size={14} className="text-green-500" />
                    <span className="text-gray-500">微信:</span>
                    <span className="font-medium">{contact.wechat}</span>
                  </div>
                )}
                {contact.phone && (
                  <div className="flex items-center gap-2">
                    <Phone size={14} className="text-blue-500" />
                    <span className="text-gray-500">手机:</span>
                    <span className="font-medium">{contact.phone}</span>
                  </div>
                )}
                {contact.email && (
                  <div className="flex items-center gap-2">
                    <Mail size={14} className="text-gray-500" />
                    <span className="text-gray-500">邮箱:</span>
                    <span className="font-medium">{contact.email}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Chat Timeline */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <MessageSquare size={18} /> 聊天记录
            </h2>
            {messages.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-6">暂无消息</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.direction === "sent" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                        msg.direction === "sent"
                          ? "bg-primary-600 text-white"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      <p>{msg.content}</p>
                      <p
                        className={`text-xs mt-1 ${
                          msg.direction === "sent"
                            ? "text-primary-200"
                            : "text-gray-400"
                        }`}
                      >
                        {msg.created_at
                          ? new Date(msg.created_at).toLocaleString("zh-CN")
                          : ""}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
