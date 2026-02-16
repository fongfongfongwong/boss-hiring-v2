import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  analyzePosition,
  createTask,
  type AnalysisResult,
} from "../api/client";
import {
  Search,
  Sparkles,
  Settings,
  Rocket,
  ChevronRight,
  ChevronLeft,
  Loader2,
  X,
  Plus,
} from "lucide-react";

const STEPS = [
  { icon: Search, label: "输入岗位" },
  { icon: Sparkles, label: "AI 分析" },
  { icon: Settings, label: "配置参数" },
  { icon: Rocket, label: "确认启动" },
];

export default function CreateTask() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Step 1
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  // Step 2 – AI result
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [editableKeywords, setEditableKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState("");

  // Step 3 – Config
  const [dailyLimit, setDailyLimit] = useState(80);
  const [threshold, setThreshold] = useState(70);
  const [autoContact, setAutoContact] = useState(true);
  const [startHour, setStartHour] = useState("09:00");
  const [endHour, setEndHour] = useState("18:00");

  async function handleAnalyze() {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const result = await analyzePosition(title, description);
      setAnalysis(result);
      const kws = [
        ...((result.keywords as any).primary_keywords || []),
        ...((result.keywords as any).skill_keywords || []),
      ];
      setEditableKeywords(kws);
      setStep(1);
    } catch (err) {
      alert("分析失败: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function addKeyword() {
    if (newKeyword.trim() && !editableKeywords.includes(newKeyword.trim())) {
      setEditableKeywords([...editableKeywords, newKeyword.trim()]);
      setNewKeyword("");
    }
  }

  function removeKeyword(kw: string) {
    setEditableKeywords(editableKeywords.filter((k) => k !== kw));
  }

  async function handleLaunch() {
    if (!analysis) return;
    setLoading(true);
    try {
      const result = await createTask(analysis.position_id, {
        greeting_daily_limit: dailyLimit,
        qualified_threshold: threshold,
        auto_contact_followup: autoContact,
        working_hours_start: startHour,
        working_hours_end: endHour,
        keywords: editableKeywords,
      });
      navigate("/");
    } catch (err) {
      alert("启动失败: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">新建招聘任务</h1>

      {/* Stepper */}
      <div className="flex items-center mb-8">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center">
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
                i === step
                  ? "bg-primary-600 text-white"
                  : i < step
                  ? "bg-primary-100 text-primary-700"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              <s.icon size={16} />
              {s.label}
            </div>
            {i < STEPS.length - 1 && (
              <ChevronRight size={16} className="mx-2 text-gray-300" />
            )}
          </div>
        ))}
      </div>

      {/* Step 0: Input */}
      {step === 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-8 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              职位名称 *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如: Quant Trader, 量化交易员, Java后端开发..."
              className="w-full px-4 py-3 border rounded-lg text-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              补充说明 (可选)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="例如: 偏高频方向, base 上海, 3年以上经验..."
              rows={3}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={!title.trim() || loading}
            className="w-full bg-primary-600 text-white py-3 rounded-lg font-medium text-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" /> AI 分析中...
              </>
            ) : (
              <>
                <Sparkles size={20} /> AI 智能分析
              </>
            )}
          </button>
        </div>
      )}

      {/* Step 1: Preview AI Results */}
      {step === 1 && analysis && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-3">AI 生成的 JD</h3>
            <div className="text-sm text-gray-700 space-y-2">
              <p>
                <strong>职位:</strong> {(analysis.jd as any).title}
              </p>
              <p>
                <strong>概述:</strong> {(analysis.jd as any).summary}
              </p>
              <div>
                <strong>职责:</strong>
                <ul className="list-disc ml-6 mt-1">
                  {((analysis.jd as any).responsibilities || []).map(
                    (r: string, i: number) => (
                      <li key={i}>{r}</li>
                    )
                  )}
                </ul>
              </div>
              <div>
                <strong>要求:</strong>
                <ul className="list-disc ml-6 mt-1">
                  {((analysis.jd as any).requirements || []).map(
                    (r: string, i: number) => (
                      <li key={i}>{r}</li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-3">搜索关键词 (可编辑)</h3>
            <div className="flex flex-wrap gap-2 mb-4">
              {editableKeywords.map((kw) => (
                <span
                  key={kw}
                  className="inline-flex items-center gap-1 bg-primary-100 text-primary-700 px-3 py-1.5 rounded-full text-sm"
                >
                  {kw}
                  <button
                    onClick={() => removeKeyword(kw)}
                    className="hover:text-red-600"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="添加关键词..."
                className="flex-1 px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
                onKeyDown={(e) => e.key === "Enter" && addKeyword()}
              />
              <button
                onClick={addKeyword}
                className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm"
              >
                <Plus size={16} />
              </button>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(0)}
              className="px-6 py-2.5 border rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-1"
            >
              <ChevronLeft size={16} /> 上一步
            </button>
            <button
              onClick={() => setStep(2)}
              className="flex-1 bg-primary-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-primary-700 flex items-center justify-center gap-1"
            >
              下一步 <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Configuration */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border p-6 space-y-5">
            <h3 className="text-lg font-semibold">运行参数配置</h3>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  每日打招呼上限
                </label>
                <input
                  type="number"
                  value={dailyLimit}
                  onChange={(e) => setDailyLimit(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  min={1}
                  max={100}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Boss直聘限制100次/天，建议设80
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  评分达标阈值
                </label>
                <input
                  type="number"
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  min={0}
                  max={100}
                />
                <p className="text-xs text-gray-400 mt-1">
                  简历AI评分 &ge; 此值则自动跟进
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  工作时段
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="time"
                    value={startHour}
                    onChange={(e) => setStartHour(e.target.value)}
                    className="px-3 py-2 border rounded-lg text-sm"
                  />
                  <span className="text-gray-400">至</span>
                  <input
                    type="time"
                    value={endHour}
                    onChange={(e) => setEndHour(e.target.value)}
                    className="px-3 py-2 border rounded-lg text-sm"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoContact}
                    onChange={(e) => setAutoContact(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-primary-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                </label>
                <span className="text-sm text-gray-700">
                  自动跟进获取联系方式
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(1)}
              className="px-6 py-2.5 border rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-1"
            >
              <ChevronLeft size={16} /> 上一步
            </button>
            <button
              onClick={() => setStep(3)}
              className="flex-1 bg-primary-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-primary-700 flex items-center justify-center gap-1"
            >
              下一步 <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Confirm & Launch */}
      {step === 3 && analysis && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
            <h3 className="text-lg font-semibold">确认并启动</h3>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-500 mb-1">职位名称</p>
                <p className="text-lg font-semibold">{title}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-500 mb-1">搜索关键词</p>
                <p>{editableKeywords.length} 个</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-500 mb-1">每日上限</p>
                <p>{dailyLimit} 次/天</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-500 mb-1">达标阈值</p>
                <p>{threshold} 分</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-500 mb-1">工作时段</p>
                <p>
                  {startHour} ~ {endHour}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-medium text-gray-500 mb-1">
                  自动获取联系方式
                </p>
                <p>{autoContact ? "开启" : "关闭"}</p>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep(2)}
              className="px-6 py-2.5 border rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-1"
            >
              <ChevronLeft size={16} /> 上一步
            </button>
            <button
              onClick={handleLaunch}
              disabled={loading}
              className="flex-1 bg-green-600 text-white py-3 rounded-lg font-medium text-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" /> 启动中...
                </>
              ) : (
                <>
                  <Rocket size={20} /> 开始招聘
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
