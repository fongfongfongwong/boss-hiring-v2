import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    found: "已发现",
    greeted: "已打招呼",
    chatting: "沟通中",
    resume_received: "已收简历",
    scored: "已评分",
    qualified: "达标",
    contact_obtained: "已获联系方式",
    rejected: "已跳过",
    archived: "已归档",
    pending: "等待中",
    running: "运行中",
    paused: "已暂停",
    completed: "已完成",
    failed: "已失败",
  };
  return map[status] || status;
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    found: "bg-gray-100 text-gray-700",
    greeted: "bg-blue-100 text-blue-700",
    chatting: "bg-yellow-100 text-yellow-700",
    resume_received: "bg-indigo-100 text-indigo-700",
    scored: "bg-purple-100 text-purple-700",
    qualified: "bg-green-100 text-green-700",
    contact_obtained: "bg-emerald-100 text-emerald-800",
    rejected: "bg-red-100 text-red-700",
    running: "bg-green-100 text-green-700",
    paused: "bg-yellow-100 text-yellow-700",
    completed: "bg-blue-100 text-blue-700",
    failed: "bg-red-100 text-red-700",
    pending: "bg-gray-100 text-gray-600",
  };
  return map[status] || "bg-gray-100 text-gray-600";
}
