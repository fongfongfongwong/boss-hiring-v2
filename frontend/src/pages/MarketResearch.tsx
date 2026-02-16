import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import {
  Globe,
  Building2,
  Briefcase,
  Users,
  Loader2,
  RefreshCw,
  Search,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Sparkles,
  TrendingUp,
  MapPin,
  FileText,
  X,
  Plus,
} from "lucide-react";

interface OpenPosition {
  title: string;
  level: string;
  location: string;
  source: string;
}

interface Company {
  id: number;
  name: string;
  name_en: string;
  region: string;
  category: string;
  website: string;
  headquarters: string;
  description: string;
  open_positions: OpenPosition[];
  open_position_count: number;
  talent_profile: string;
  supplementary_info: string;
  boss_resume_count: number;
  last_researched_at: string | null;
}

interface Summary {
  total_companies: number;
  cn_companies: number;
  us_companies: number;
  categories: Record<string, number>;
  researched_count: number;
  total_open_positions: number;
}

const CATEGORY_LABELS: Record<string, string> = {
  quant: "量化",
  prop_trading: "自营交易",
  hedge_fund: "对冲基金",
  market_maker: "做市商",
  other: "其他",
};

const REGION_FLAGS: Record<string, string> = {
  CN: "CN",
  US: "US",
  Global: "Global",
};

export default function MarketResearch() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [researchingAll, setResearchingAll] = useState(false);
  const [researchingId, setResearchingId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [filterRegion, setFilterRegion] = useState<string>("");
  const [filterCategory, setFilterCategory] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [report, setReport] = useState("");
  const [generatingReport, setGeneratingReport] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCompany, setNewCompany] = useState({
    name: "",
    name_en: "",
    region: "CN",
    category: "quant",
    website: "",
    headquarters: "",
    description: "",
  });

  const loadData = useCallback(async () => {
    try {
      const [companiesData, summaryData] = await Promise.all([
        api.get<Company[]>(
          `/api/market/companies${filterRegion ? `?region=${filterRegion}` : ""}${
            filterCategory
              ? `${filterRegion ? "&" : "?"}category=${filterCategory}`
              : ""
          }`
        ),
        api.get<Summary>("/api/market/summary"),
      ]);
      setCompanies(companiesData);
      setSummary(summaryData);
    } catch (err) {
      console.error("Failed to load market data:", err);
    } finally {
      setLoading(false);
    }
  }, [filterRegion, filterCategory]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Polling for task status
  useEffect(() => {
    if (!seeding && !researchingAll && researchingId === null) return;
    const interval = setInterval(async () => {
      try {
        const status = await api.get<Record<string, { status: string }>>(
          "/api/market/task-status"
        );
        if (seeding && status.seed?.status !== "running") {
          setSeeding(false);
          loadData();
        }
        if (researchingAll && status.research_all?.status !== "running") {
          setResearchingAll(false);
          loadData();
        }
        if (
          researchingId !== null &&
          status[`research_${researchingId}`]?.status !== "running"
        ) {
          setResearchingId(null);
          loadData();
        }
      } catch {
        /* ignore */
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [seeding, researchingAll, researchingId, loadData]);

  async function handleSeed() {
    setSeeding(true);
    try {
      await api.post("/api/market/seed");
    } catch (err) {
      alert("启动失败: " + (err as Error).message);
      setSeeding(false);
    }
  }

  async function handleResearchAll() {
    setResearchingAll(true);
    try {
      await api.post("/api/market/research-all");
    } catch (err) {
      alert("启动失败: " + (err as Error).message);
      setResearchingAll(false);
    }
  }

  async function handleResearchSingle(id: number) {
    setResearchingId(id);
    try {
      await api.post(`/api/market/companies/${id}/research`);
    } catch (err) {
      alert("调研失败: " + (err as Error).message);
      setResearchingId(null);
    }
  }

  async function handleGenerateReport() {
    setGeneratingReport(true);
    try {
      const result = await api.post<{ report: string }>(
        "/api/market/generate-report"
      );
      setReport(result.report);
      setShowReport(true);
    } catch (err) {
      alert("生成报告失败: " + (err as Error).message);
    } finally {
      setGeneratingReport(false);
    }
  }

  async function handleAddCompany() {
    if (!newCompany.name.trim()) return;
    try {
      await api.post("/api/market/companies", newCompany);
      setShowAddForm(false);
      setNewCompany({
        name: "",
        name_en: "",
        region: "CN",
        category: "quant",
        website: "",
        headquarters: "",
        description: "",
      });
      loadData();
    } catch (err) {
      alert("添加失败: " + (err as Error).message);
    }
  }

  async function handleDeleteCompany(id: number) {
    if (!confirm("确定删除该公司？")) return;
    try {
      await api.delete(`/api/market/companies/${id}`);
      loadData();
    } catch (err) {
      alert("删除失败: " + (err as Error).message);
    }
  }

  const filteredCompanies = companies.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.name.toLowerCase().includes(q) ||
      c.name_en.toLowerCase().includes(q) ||
      c.headquarters.toLowerCase().includes(q)
    );
  });

  const cnCompanies = filteredCompanies.filter((c) => c.region === "CN");
  const usCompanies = filteredCompanies.filter((c) => c.region === "US");

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Globe size={24} />
            量化/交易市场调研
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            中美量化公司招聘动态与人才画像 Overview
          </p>
        </div>
        <div className="flex gap-2">
          {companies.length === 0 ? (
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
            >
              {seeding ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Sparkles size={16} />
              )}
              {seeding ? "AI 生成中..." : "AI 生成公司列表"}
            </button>
          ) : (
            <>
              <button
                onClick={() => setShowAddForm(true)}
                className="border border-gray-300 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-1.5"
              >
                <Plus size={15} />
                添加公司
              </button>
              <button
                onClick={handleResearchAll}
                disabled={researchingAll}
                className="border border-gray-300 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1.5"
              >
                {researchingAll ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <RefreshCw size={15} />
                )}
                {researchingAll ? "调研中..." : "全部调研"}
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={generatingReport}
                className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
              >
                {generatingReport ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <FileText size={16} />
                )}
                {generatingReport ? "生成中..." : "生成报告"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      {summary && summary.total_companies > 0 && (
        <div className="grid grid-cols-5 gap-3">
          {[
            {
              label: "追踪公司",
              value: summary.total_companies,
              icon: Building2,
            },
            { label: "中国公司", value: summary.cn_companies, icon: MapPin },
            { label: "美国公司", value: summary.us_companies, icon: Globe },
            {
              label: "在招岗位",
              value: summary.total_open_positions,
              icon: Briefcase,
            },
            {
              label: "已调研",
              value: summary.researched_count,
              icon: Search,
            },
          ].map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="bg-white rounded-xl border p-4 flex items-center gap-3"
            >
              <div className="p-2 bg-primary-50 rounded-lg">
                <Icon size={18} className="text-primary-600" />
              </div>
              <div>
                <div className="text-xl font-bold">{value}</div>
                <div className="text-xs text-gray-400">{label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      {companies.length > 0 && (
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索公司名称..."
              className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <select
            value={filterRegion}
            onChange={(e) => {
              setFilterRegion(e.target.value);
              setLoading(true);
            }}
            className="border rounded-lg px-3 py-2 text-sm bg-white"
          >
            <option value="">全部地区</option>
            <option value="CN">中国</option>
            <option value="US">美国</option>
          </select>
          <select
            value={filterCategory}
            onChange={(e) => {
              setFilterCategory(e.target.value);
              setLoading(true);
            }}
            className="border rounded-lg px-3 py-2 text-sm bg-white"
          >
            <option value="">全部类型</option>
            <option value="quant">量化</option>
            <option value="prop_trading">自营交易</option>
            <option value="hedge_fund">对冲基金</option>
            <option value="market_maker">做市商</option>
          </select>
        </div>
      )}

      {/* Add Company Form Modal */}
      {showAddForm && (
        <div className="bg-white rounded-xl border shadow-sm p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm">手动添加公司</h3>
            <button
              onClick={() => setShowAddForm(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={16} />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              value={newCompany.name}
              onChange={(e) =>
                setNewCompany({ ...newCompany, name: e.target.value })
              }
              placeholder="公司名称 *"
              className="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
            />
            <input
              type="text"
              value={newCompany.name_en}
              onChange={(e) =>
                setNewCompany({ ...newCompany, name_en: e.target.value })
              }
              placeholder="英文名称"
              className="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
            />
            <select
              value={newCompany.region}
              onChange={(e) =>
                setNewCompany({ ...newCompany, region: e.target.value })
              }
              className="px-3 py-2 border rounded-lg text-sm bg-white"
            >
              <option value="CN">中国</option>
              <option value="US">美国</option>
              <option value="Global">全球</option>
            </select>
            <select
              value={newCompany.category}
              onChange={(e) =>
                setNewCompany({ ...newCompany, category: e.target.value })
              }
              className="px-3 py-2 border rounded-lg text-sm bg-white"
            >
              <option value="quant">量化</option>
              <option value="prop_trading">自营交易</option>
              <option value="hedge_fund">对冲基金</option>
              <option value="market_maker">做市商</option>
            </select>
            <input
              type="text"
              value={newCompany.website}
              onChange={(e) =>
                setNewCompany({ ...newCompany, website: e.target.value })
              }
              placeholder="官网 URL"
              className="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
            />
            <input
              type="text"
              value={newCompany.headquarters}
              onChange={(e) =>
                setNewCompany({ ...newCompany, headquarters: e.target.value })
              }
              placeholder="总部城市"
              className="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button
            onClick={handleAddCompany}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            添加
          </button>
        </div>
      )}

      {/* Company Sections */}
      {companies.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Globe size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium mb-2">暂无公司数据</p>
          <p className="text-sm mb-6">
            点击"AI 生成公司列表"自动生成中美量化/交易公司清单
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* CN Companies */}
          {cnCompanies.length > 0 && (
            <CompanySection
              title="中国量化/交易公司"
              region="CN"
              companies={cnCompanies}
              expandedId={expandedId}
              setExpandedId={setExpandedId}
              researchingId={researchingId}
              onResearch={handleResearchSingle}
              onDelete={handleDeleteCompany}
            />
          )}

          {/* US Companies */}
          {usCompanies.length > 0 && (
            <CompanySection
              title="美国量化/交易公司"
              region="US"
              companies={usCompanies}
              expandedId={expandedId}
              setExpandedId={setExpandedId}
              researchingId={researchingId}
              onResearch={handleResearchSingle}
              onDelete={handleDeleteCompany}
            />
          )}
        </div>
      )}

      {/* Report Modal */}
      {showReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-2xl shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <FileText size={20} />
                市场调研报告
              </h2>
              <button
                onClick={() => setShowReport(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-auto px-6 py-4">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                {report}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Company Section Component ───────────────────────────────────────

function CompanySection({
  title,
  region,
  companies,
  expandedId,
  setExpandedId,
  researchingId,
  onResearch,
  onDelete,
}: {
  title: string;
  region: string;
  companies: Company[];
  expandedId: number | null;
  setExpandedId: (id: number | null) => void;
  researchingId: number | null;
  onResearch: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <div>
      <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <span
          className={`text-xs font-bold px-2 py-0.5 rounded ${
            region === "CN"
              ? "bg-red-100 text-red-700"
              : "bg-blue-100 text-blue-700"
          }`}
        >
          {REGION_FLAGS[region] || region}
        </span>
        {title}
        <span className="text-sm font-normal text-gray-400">
          ({companies.length})
        </span>
      </h2>
      <div className="space-y-2">
        {companies.map((c) => (
          <CompanyCard
            key={c.id}
            company={c}
            isExpanded={expandedId === c.id}
            onToggle={() =>
              setExpandedId(expandedId === c.id ? null : c.id)
            }
            isResearching={researchingId === c.id}
            onResearch={() => onResearch(c.id)}
            onDelete={() => onDelete(c.id)}
          />
        ))}
      </div>
    </div>
  );
}

// ── Company Card Component ──────────────────────────────────────────

function CompanyCard({
  company: c,
  isExpanded,
  onToggle,
  isResearching,
  onResearch,
  onDelete,
}: {
  company: Company;
  isExpanded: boolean;
  onToggle: () => void;
  isResearching: boolean;
  onResearch: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
      {/* Card Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="shrink-0">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <Building2 size={16} className="text-primary-600" />
            </div>
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm truncate">{c.name}</span>
              {c.name_en && (
                <span className="text-xs text-gray-400 truncate">
                  {c.name_en}
                </span>
              )}
              <span
                className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                  c.category === "quant"
                    ? "bg-purple-50 text-purple-600"
                    : c.category === "prop_trading"
                    ? "bg-orange-50 text-orange-600"
                    : c.category === "hedge_fund"
                    ? "bg-green-50 text-green-600"
                    : "bg-blue-50 text-blue-600"
                }`}
              >
                {CATEGORY_LABELS[c.category] || c.category}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
              {c.headquarters && (
                <span className="flex items-center gap-1">
                  <MapPin size={11} />
                  {c.headquarters}
                </span>
              )}
              {c.description && <span className="truncate max-w-[300px]">{c.description}</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {c.open_position_count > 0 && (
            <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-lg font-medium">
              {c.open_position_count} 在招
            </span>
          )}
          {c.last_researched_at ? (
            <span className="text-[10px] text-gray-400">
              已调研
            </span>
          ) : (
            <span className="text-[10px] text-yellow-500">待调研</span>
          )}
          {isExpanded ? (
            <ChevronUp size={16} className="text-gray-400" />
          ) : (
            <ChevronDown size={16} className="text-gray-400" />
          )}
        </div>
      </div>

      {/* Expanded Detail */}
      {isExpanded && (
        <div className="border-t px-4 py-4 space-y-4 bg-gray-50/50">
          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onResearch();
              }}
              disabled={isResearching}
              className="bg-primary-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center gap-1.5"
            >
              {isResearching ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <Search size={13} />
              )}
              {isResearching ? "调研中..." : "AI 深度调研"}
            </button>
            {c.website && (
              <a
                href={c.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1 px-2 py-1.5 border rounded-lg hover:bg-primary-50"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink size={13} />
                官网
              </a>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="text-xs text-red-500 hover:text-red-600 px-2 py-1.5 border border-red-200 rounded-lg hover:bg-red-50 ml-auto"
            >
              删除
            </button>
          </div>

          {/* Open Positions */}
          {c.open_positions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <Briefcase size={13} />
                在招岗位 ({c.open_positions.length})
              </h4>
              <div className="grid grid-cols-2 gap-1.5">
                {c.open_positions.map((p, i) => (
                  <div
                    key={i}
                    className="text-xs bg-white border rounded-lg px-3 py-2 flex items-center justify-between"
                  >
                    <span className="font-medium text-gray-700">{p.title}</span>
                    <div className="flex items-center gap-2 text-gray-400">
                      {p.level && (
                        <span className="bg-gray-100 px-1.5 py-0.5 rounded">
                          {p.level}
                        </span>
                      )}
                      {p.location && <span>{p.location}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Talent Profile */}
          {c.talent_profile && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <Users size={13} />
                人才画像
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap bg-white border rounded-lg p-3">
                {c.talent_profile}
              </p>
            </div>
          )}

          {/* Supplementary Info */}
          {c.supplementary_info && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <TrendingUp size={13} />
                补充信息 / 最新动态
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap bg-white border rounded-lg p-3">
                {c.supplementary_info}
              </p>
            </div>
          )}

          {/* No data yet */}
          {!c.talent_profile && !c.supplementary_info && c.open_positions.length === 0 && (
            <div className="text-center py-6 text-gray-400 text-sm">
              <Search size={24} className="mx-auto mb-2 opacity-30" />
              暂无调研数据，请点击"AI 深度调研"获取
            </div>
          )}
        </div>
      )}
    </div>
  );
}
