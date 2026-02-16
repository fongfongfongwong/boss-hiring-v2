/**
 * API client – wraps fetch for backend communication.
 */

const BASE = "";

async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const resp = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API Error ${resp.status}: ${text}`);
  }
  return resp.json();
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, body?: unknown) =>
    request<T>(url, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(url: string, body?: unknown) =>
    request<T>(url, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(url: string) => request<T>(url, { method: "DELETE" }),
};

// ── Typed API functions ──────────────────────────────────────────────

export interface DashboardStats {
  total_positions: number;
  total_tasks: number;
  active_tasks: number;
  total_candidates: number;
  greeted: number;
  resume_received: number;
  qualified: number;
  contact_obtained: number;
}

export interface FunnelStage {
  stage: string;
  count: number;
}

export interface TaskSummary {
  id: number;
  position_id: number;
  position_title: string;
  status: string;
  progress: Record<string, number>;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface CandidateSummary {
  id: number;
  task_id: number;
  position_id: number;
  name: string;
  status: string;
  pre_match_score: number;
  resume_score: number | null;
  is_qualified: boolean | null;
  has_contact: boolean;
  created_at: string | null;
}

export interface PositionSummary {
  id: number;
  title: string;
  description: string;
  created_at: string | null;
  candidate_count: number;
}

export interface AnalysisResult {
  position_id: number;
  title: string;
  jd: Record<string, unknown>;
  keywords: Record<string, unknown>;
  filters: Record<string, unknown>;
  scorecard: Record<string, unknown>;
}

export const fetchDashboardStats = () =>
  api.get<DashboardStats>("/api/dashboard/stats");

export const fetchFunnel = (taskId: number) =>
  api.get<{ funnel: FunnelStage[]; position_title: string }>(
    `/api/dashboard/funnel/${taskId}`
  );

export const fetchTasks = () => api.get<TaskSummary[]>("/api/tasks");

export const fetchCandidates = (params?: string) =>
  api.get<{ total: number; items: CandidateSummary[] }>(
    `/api/candidates${params ? `?${params}` : ""}`
  );

export const fetchCandidate = (id: number) =>
  api.get<Record<string, unknown>>(`/api/candidates/${id}`);

export const fetchCandidateMessages = (id: number) =>
  api.get<
    { id: number; direction: string; content: string; message_type: string; created_at: string }[]
  >(`/api/candidates/${id}/messages`);

export const fetchPositions = () =>
  api.get<PositionSummary[]>("/api/positions");

export const analyzePosition = (title: string, description: string) =>
  api.post<AnalysisResult>("/api/positions/analyze", { title, description });

export const createTask = (positionId: number, config: Record<string, unknown>) =>
  api.post<{ task_id: number }>("/api/tasks", {
    position_id: positionId,
    config,
  });

export const pauseTask = (id: number) => api.post(`/api/tasks/${id}/pause`);
export const resumeTask = (id: number) => api.post(`/api/tasks/${id}/resume`);
export const stopTask = (id: number) => api.post(`/api/tasks/${id}/stop`);
