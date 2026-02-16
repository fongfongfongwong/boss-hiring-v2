import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import {
  Settings as SettingsIcon,
  Check,
  Loader2,
  Wifi,
  Shield,
  AlertCircle,
  UserPlus,
  RefreshCw,
  Trash2,
  Smartphone,
  LogIn,
  Building2,
} from "lucide-react";

interface Provider {
  id: string;
  name: string;
  base_url: string;
  models: { id: string; name: string; context: string }[];
}

interface CurrentSettings {
  api_key_masked: string;
  has_api_key: boolean;
  base_url: string;
  model: string;
  current_provider: string;
  boss_logged_in: boolean;
}

interface BossAccount {
  id: number;
  name: string;
  phone: string;
  company: string;
  is_logged_in: boolean;
  is_logging_in: boolean;
  last_login_at: string | null;
  created_at: string | null;
}

export default function Settings() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [current, setCurrent] = useState<CurrentSettings | null>(null);
  const [loading, setLoading] = useState(true);

  // Form state
  const [selectedProvider, setSelectedProvider] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [customModel, setCustomModel] = useState("");

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  // Boss accounts state
  const [bossAccounts, setBossAccounts] = useState<BossAccount[]>([]);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginMessage, setLoginMessage] = useState("");
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [pollingAccountId, setPollingAccountId] = useState<number | null>(null);

  const loadBossAccounts = useCallback(async () => {
    try {
      const data = await api.get<BossAccount[]>("/api/boss-accounts");
      setBossAccounts(data);
    } catch (err) {
      console.error("Failed to load boss accounts:", err);
    }
  }, []);

  useEffect(() => {
    loadSettings();
    loadBossAccounts();
  }, [loadBossAccounts]);

  async function loadSettings() {
    try {
      const [settingsData, providersData] = await Promise.all([
        api.get<CurrentSettings>("/api/settings"),
        api.get<Provider[]>("/api/settings/providers"),
      ]);
      setCurrent(settingsData);
      setProviders(providersData);

      // Initialize form from current settings
      setSelectedProvider(settingsData.current_provider);
      setBaseUrl(settingsData.base_url);
      setModel(settingsData.model);

      // If current model is not in any provider's list, set it as custom
      const provider = providersData.find(
        (p) => p.id === settingsData.current_provider
      );
      if (
        provider &&
        provider.models.length > 0 &&
        !provider.models.find((m) => m.id === settingsData.model)
      ) {
        setCustomModel(settingsData.model);
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  }

  function handleProviderChange(providerId: string) {
    setSelectedProvider(providerId);
    const provider = providers.find((p) => p.id === providerId);
    if (provider) {
      if (provider.base_url) {
        setBaseUrl(provider.base_url);
      }
      if (provider.models.length > 0) {
        setModel(provider.models[0].id);
        setCustomModel("");
      }
    }
    setTestResult(null);
  }

  function handleModelChange(modelId: string) {
    setModel(modelId);
    setCustomModel("");
    setTestResult(null);
  }

  const currentProvider = providers.find((p) => p.id === selectedProvider);
  const availableModels = currentProvider?.models || [];
  const isCustom = selectedProvider === "custom";
  const finalModel = isCustom || customModel ? customModel || model : model;

  async function handleSave() {
    setSaving(true);
    setTestResult(null);
    try {
      await api.put("/api/settings", {
        api_key: apiKey || undefined,
        base_url: baseUrl,
        model: finalModel,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      // Reload to get updated masked key
      await loadSettings();
      setApiKey("");
    } catch (err) {
      alert("保存失败: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.post<{
        success: boolean;
        response?: string;
        error?: string;
        model?: string;
      }>("/api/settings/test");
      if (result.success) {
        setTestResult({
          success: true,
          message: `连接成功! 模型: ${result.model} — "${result.response}"`,
        });
      } else {
        setTestResult({
          success: false,
          message: `连接失败: ${result.error}`,
        });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: `请求错误: ${(err as Error).message}`,
      });
    } finally {
      setTesting(false);
    }
  }

  // Poll for login status when a login is in progress
  useEffect(() => {
    if (pollingAccountId === null) return;
    pollingRef.current = setInterval(async () => {
      try {
        const status = await api.get<{
          account_id: number;
          is_logged_in: boolean;
          is_logging_in: boolean;
          name: string;
          company: string;
          step: string;
        }>(`/api/boss-accounts/${pollingAccountId}/status`);

        if (status.is_logged_in) {
          setLoginMessage("登录成功! " + (status.name || "") + (status.company ? ` (${status.company})` : ""));
          setPollingAccountId(null);
          setLoginLoading(false);
          loadBossAccounts();
        } else if (!status.is_logging_in) {
          setLoginMessage("浏览器已关闭。如未登录成功，请重试。");
          setPollingAccountId(null);
          setLoginLoading(false);
          loadBossAccounts();
        } else {
          const stepMap: Record<string, string> = {
            launching: "正在启动浏览器...",
            navigating: "正在打开 Boss 直聘...",
            waiting_for_login: "等待手机号登录中... 请在 Chrome 窗口中完成登录",
            login_success: "登录成功，正在保存...",
          };
          setLoginMessage(stepMap[status.step] || "处理中...");
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [pollingAccountId, loadBossAccounts]);

  async function handleAddAccount() {
    setLoginLoading(true);
    setLoginMessage("正在启动 Chrome 浏览器...");
    try {
      const result = await api.post<{
        account_id: number;
        status: string;
        message: string;
      }>("/api/boss-accounts/login", { name: "" });
      setLoginMessage(result.message);
      setPollingAccountId(result.account_id);
    } catch (err) {
      setLoginMessage("启动失败: " + (err as Error).message);
      setLoginLoading(false);
    }
  }

  async function handleRelogin(accountId: number) {
    setLoginLoading(true);
    setLoginMessage("正在重新打开浏览器...");
    try {
      const result = await api.post<{
        account_id: number;
        status: string;
        message: string;
      }>(`/api/boss-accounts/${accountId}/relogin`);
      setLoginMessage(result.message);
      if (result.status !== "already_logging_in") {
        setPollingAccountId(accountId);
      }
    } catch (err) {
      setLoginMessage("启动失败: " + (err as Error).message);
      setLoginLoading(false);
    }
  }

  async function handleDeleteAccount(accountId: number) {
    if (!confirm("确定删除该账号？浏览器登录数据将被清除。")) return;
    try {
      await api.delete(`/api/boss-accounts/${accountId}`);
      loadBossAccounts();
    } catch (err) {
      alert("删除失败: " + (err as Error).message);
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <SettingsIcon size={24} /> 系统设置
      </h1>

      {/* LLM Provider Selection */}
      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-5">
        <h2 className="text-lg font-semibold">LLM 模型配置</h2>

        {/* Provider */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            选择服务商
          </label>
          <div className="grid grid-cols-3 gap-2">
            {providers.map((p) => (
              <button
                key={p.id}
                onClick={() => handleProviderChange(p.id)}
                className={`px-3 py-2.5 rounded-lg border text-sm font-medium transition-all text-left ${
                  selectedProvider === p.id
                    ? "border-primary-500 bg-primary-50 text-primary-700 ring-1 ring-primary-500"
                    : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            API Key
          </label>
          {current?.has_api_key && !apiKey && (
            <div className="flex items-center gap-2 mb-2">
              <Shield size={14} className="text-green-500" />
              <span className="text-xs text-green-600">
                当前已配置: {current.api_key_masked}
              </span>
            </div>
          )}
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={
              current?.has_api_key ? "留空保持不变，或输入新 Key..." : "sk-..."
            }
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {/* Base URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            API Base URL
          </label>
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://api.example.com/v1"
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          {currentProvider && currentProvider.base_url && (
            <p className="text-xs text-gray-400 mt-1">
              {currentProvider.name} 默认地址: {currentProvider.base_url}
            </p>
          )}
        </div>

        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            模型
          </label>
          {availableModels.length > 0 ? (
            <div className="space-y-2">
              <div className="grid grid-cols-1 gap-1.5">
                {availableModels.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => handleModelChange(m.id)}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-lg border text-sm transition-all ${
                      model === m.id && !customModel
                        ? "border-primary-500 bg-primary-50 text-primary-700 ring-1 ring-primary-500"
                        : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <span className="font-medium">{m.name}</span>
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      {m.context}
                    </span>
                  </button>
                ))}
              </div>
              <div className="pt-1">
                <input
                  type="text"
                  value={customModel}
                  onChange={(e) => {
                    setCustomModel(e.target.value);
                    if (e.target.value) setModel(e.target.value);
                  }}
                  placeholder="或输入自定义模型名称..."
                  className="w-full px-3 py-2 border border-dashed rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-gray-500"
                />
              </div>
            </div>
          ) : (
            <input
              type="text"
              value={customModel || model}
              onChange={(e) => {
                setCustomModel(e.target.value);
                setModel(e.target.value);
              }}
              placeholder="输入模型名称 (如 gpt-4o, moonshot-v1-128k...)"
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          )}
        </div>

        {/* Test Result */}
        {testResult && (
          <div
            className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
              testResult.success
                ? "bg-green-50 text-green-700 border border-green-200"
                : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            {testResult.success ? (
              <Wifi size={16} className="mt-0.5 shrink-0" />
            ) : (
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
            )}
            <span>{testResult.message}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-primary-600 text-white px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {saving ? (
              <Loader2 size={16} className="animate-spin" />
            ) : saved ? (
              <Check size={16} />
            ) : null}
            {saved ? "已保存" : "保存配置"}
          </button>
          <button
            onClick={handleTest}
            disabled={testing}
            className="border border-gray-300 text-gray-700 px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {testing ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Wifi size={16} />
            )}
            {testing ? "测试中..." : "测试连接"}
          </button>
        </div>
      </div>

      {/* Boss Zhipin Account Management */}
      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Building2 size={20} />
            Boss 直聘账号管理
          </h2>
          <button
            onClick={handleAddAccount}
            disabled={loginLoading}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium text-sm hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {loginLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <UserPlus size={16} />
            )}
            {loginLoading ? "登录中..." : "添加新账号"}
          </button>
        </div>

        <p className="text-sm text-gray-500">
          点击"添加新账号"将打开 Chrome 浏览器，请在弹出窗口中用手机号登录 Boss 直聘招聘者账号。支持同时管理多个账号。
        </p>

        {/* Login progress message */}
        {loginMessage && (
          <div
            className={`flex items-center gap-2 p-3 rounded-lg text-sm ${
              loginMessage.includes("成功")
                ? "bg-green-50 text-green-700 border border-green-200"
                : loginMessage.includes("失败") || loginMessage.includes("关闭")
                ? "bg-yellow-50 text-yellow-700 border border-yellow-200"
                : "bg-blue-50 text-blue-700 border border-blue-200"
            }`}
          >
            {loginLoading && <Loader2 size={14} className="animate-spin shrink-0" />}
            {!loginLoading && loginMessage.includes("成功") && <Check size={14} className="shrink-0" />}
            {!loginLoading && !loginMessage.includes("成功") && <Smartphone size={14} className="shrink-0" />}
            <span>{loginMessage}</span>
          </div>
        )}

        {/* Account list */}
        {bossAccounts.length > 0 ? (
          <div className="space-y-2">
            {bossAccounts.map((acct) => (
              <div
                key={acct.id}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                      acct.is_logging_in
                        ? "bg-blue-400 animate-pulse"
                        : acct.is_logged_in
                        ? "bg-green-400"
                        : "bg-gray-300"
                    }`}
                  />
                  <div>
                    <div className="text-sm font-medium text-gray-800">
                      {acct.name || `账号 ${acct.id}`}
                      {acct.company && (
                        <span className="text-gray-400 font-normal ml-2">
                          {acct.company}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {acct.is_logging_in ? (
                        <span className="text-blue-500">正在登录中...</span>
                      ) : acct.is_logged_in ? (
                        <span className="text-green-600">
                          已登录
                          {acct.last_login_at &&
                            ` · ${new Date(acct.last_login_at).toLocaleString("zh-CN")}`}
                        </span>
                      ) : (
                        <span className="text-gray-400">未登录</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleRelogin(acct.id)}
                    disabled={loginLoading}
                    className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors disabled:opacity-30"
                    title="重新登录"
                  >
                    <LogIn size={16} />
                  </button>
                  <button
                    onClick={() => handleDeleteAccount(acct.id)}
                    disabled={loginLoading}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-30"
                    title="删除账号"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">
            <Smartphone size={32} className="mx-auto mb-2 opacity-30" />
            暂无 Boss 直聘账号，请点击上方按钮添加
          </div>
        )}

        {/* Refresh button */}
        {bossAccounts.length > 0 && (
          <button
            onClick={loadBossAccounts}
            className="text-sm text-gray-400 hover:text-gray-600 flex items-center gap-1 transition-colors"
          >
            <RefreshCw size={14} />
            刷新状态
          </button>
        )}
      </div>

      {/* Current Config Summary */}
      {current?.has_api_key && (
        <div className="bg-gray-50 rounded-xl border border-dashed p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            当前运行配置
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-400">服务商</span>
              <p className="font-medium">
                {providers.find((p) => p.id === current.current_provider)
                  ?.name || "自定义"}
              </p>
            </div>
            <div>
              <span className="text-gray-400">模型</span>
              <p className="font-medium">{current.model}</p>
            </div>
            <div>
              <span className="text-gray-400">API Key</span>
              <p className="font-medium">{current.api_key_masked}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
