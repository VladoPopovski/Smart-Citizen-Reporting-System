import { supabase } from "@/lib/supabase";
import { apiFetch } from "./api";

export interface HistoryRead {
  id: string | number;
  old_status_id: number | null;
  status_id: number | null;
  changed_by_user_id: string | null;
  created_at: string;
}

export interface CommentRead {
  id: string | number;
  user_id: string;
  content: string;
  created_at: string;
}

export interface ReportRead {
  id: string;
  description: string;
  priority?: string | null;
  latitude: number | null;
  longitude: number | null;
  category_id: number | null;
  status_id: number | null;
  user_id: string;
  created_at: string;
  ai_confirmation_text?: string | null;
  possible_duplicate_of?: string | null;
  history_entries: HistoryRead[];
  comments: CommentRead[];
}

export interface ReportCreate {
  description: string;
  latitude: number | null;
  longitude: number | null;
  category_id?: number | null;
  status_id?: number | null;
}

export type PriorityValue = "Низок" | "Среден" | "Висок" | "Итен";

interface AnalyzeReportResponse {
  category_id: number | null;
  priority: string | null;
  ai_confirmation_text: string | null;
}

function fallbackCategoryId(description: string): number {
  const text = description.toLowerCase();
  if (["fire", "smoke", "injur", "accident", "danger", "unsafe", "emergency", "explosion", "flood", "hazard"].some((k) => text.includes(k))) {
    return 3;
  }
  if (["pothole", "road", "street", "light", "lamp", "sidewalk", "bridge", "broken", "hole", "infrastructure", "sewer", "pipe"].some((k) => text.includes(k))) {
    return 1;
  }
  if (["trash", "garbage", "waste", "litter", "pollution", "tree", "park", "smell", "environment", "dump"].some((k) => text.includes(k))) {
    return 2;
  }
  return 4;
}

function fallbackPriority(description: string): PriorityValue {
  const text = description.toLowerCase();
  if (["fire", "injur", "accident", "danger", "unsafe", "emergency", "explosion", "flood", "hazard"].some((k) => text.includes(k))) {
    return "Итен";
  }
  if (["broken", "blocked", "overflow", "leak", "sewer", "dark", "no light"].some((k) => text.includes(k))) {
    return "Висок";
  }
  return "Среден";
}

function normalizeReport(row: any): ReportRead {
  return {
    id: row.id,
    description: row.description,
    priority: row.priority ?? null,
    latitude: row.latitude ?? null,
    longitude: row.longitude ?? null,
    category_id: row.category_id ?? null,
    status_id: row.status_id ?? null,
    user_id: row.user_id,
    created_at: row.created_at,
    ai_confirmation_text: row.ai_confirmation_text ?? null,
    possible_duplicate_of: row.possible_duplicate_of ?? null,
    history_entries: [],
    comments: [],
  };
}

async function getCurrentUserId(): Promise<string> {
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error) {
    throw new Error(error.message || "Failed to read authenticated user.");
  }

  if (!user?.id) {
    throw new Error("Not authenticated.");
  }

  return user.id;
}

export async function fetchReports(): Promise<ReportRead[]> {
  const { data, error } = await supabase
    .from("reports")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    throw new Error(error.message || "Failed to fetch reports.");
  }

  return (data ?? []).map(normalizeReport);
}

export async function fetchReportById(id: string): Promise<ReportRead> {
  const { data, error } = await supabase
    .from("reports")
    .select("*")
    .eq("id", id)
    .single();

  if (error) {
    throw new Error(error.message || "Failed to fetch report.");
  }

  const report = normalizeReport(data);
  report.comments = await fetchReportComments(id);
  report.history_entries = await fetchReportHistory(id);
  return report;
}

export async function createReport(data: ReportCreate): Promise<ReportRead> {
  const userId = await getCurrentUserId();

  let analysis: AnalyzeReportResponse | null = null;
  try {
    analysis = await apiFetch<AnalyzeReportResponse>("/ai/analyze-report", {
      method: "POST",
      body: JSON.stringify({
        description: data.description,
        category_id: data.category_id ?? null,
      }),
    });
  } catch {
    analysis = {
      category_id: data.category_id ?? fallbackCategoryId(data.description),
      priority: fallbackPriority(data.description),
      ai_confirmation_text: null,
    };
  }

  const payload = {
    description: data.description,
    latitude: data.latitude,
    longitude: data.longitude,
    category_id: analysis?.category_id ?? data.category_id ?? null,
    status_id: data.status_id ?? null,
    priority: analysis?.priority ?? null,
    ai_confirmation_text: analysis?.ai_confirmation_text ?? null,
    user_id: userId,
  };

  const { data: inserted, error } = await supabase
    .from("reports")
    .insert(payload)
    .select("*")
    .single();

  if (error) {
    throw new Error(error.message || "Failed to create report.");
  }

  return normalizeReport(inserted);
}

export async function addComment(reportId: string, content: string): Promise<CommentRead> {
  const userId = await getCurrentUserId();
  const { data, error } = await supabase
    .from("comments")
    .insert({ report_id: reportId, content, user_id: userId })
    .select("id, user_id, content, created_at")
    .single();

  if (error) {
    throw new Error(error.message || "Failed to add comment.");
  }

  return data;
}

export async function updateReport(reportId: string, patch: Partial<Pick<ReportRead, "description" | "latitude" | "longitude" | "category_id" | "status_id" | "priority">>): Promise<ReportRead> {
  const { data, error } = await supabase
    .from("reports")
    .update(patch)
    .eq("id", reportId)
    .select("*")
    .single();

  if (error) {
    throw new Error(error.message || "Failed to update report.");
  }

  return normalizeReport(data);
}

export function updateReportPriority(reportId: string, priority: PriorityValue): Promise<ReportRead> {
  return updateReport(reportId, { priority });
}

export async function fetchReportComments(reportId: string): Promise<CommentRead[]> {
  const { data, error } = await supabase
    .from("comments")
    .select("id, user_id, content, created_at")
    .eq("report_id", reportId)
    .order("created_at", { ascending: true });

  if (error) {
    if (error.code === "42P01") return [];
    throw new Error(error.message || "Failed to fetch comments.");
  }

  return data ?? [];
}

export async function fetchReportHistory(reportId: string): Promise<HistoryRead[]> {
  const { data, error } = await supabase
    .from("history")
    .select("id, old_status_id, status_id, changed_by_user_id, created_at")
    .eq("report_id", reportId)
    .order("created_at", { ascending: true });

  if (error) {
    if (error.code === "42P01") return [];
    throw new Error(error.message || "Failed to fetch history.");
  }

  return data ?? [];
}
