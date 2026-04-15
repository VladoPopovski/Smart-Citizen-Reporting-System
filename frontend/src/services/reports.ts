import { apiFetch } from "./api";

export interface HistoryRead {
  id: number;
  old_status_id: number | null;
  status_id: number | null;
  changed_by_user_id: string | null;
  created_at: string;
}

export interface CommentRead {
  id: number;
  user_id: string;
  content: string;
  created_at: string;
}

export interface ReportRead {
  id: number;
  description: string;
  latitude: number | null;
  longitude: number | null;
  category_id: number | null;
  status_id: number | null;
  user_id: string;
  created_at: string;
  possible_duplicate_of: number | null;
  history_entries: HistoryRead[];
  comments: CommentRead[];
}

export interface ReportCreate {
  description: string;
  latitude: number | null;
  longitude: number | null;
  category_id?: number | null;
}

export function fetchReports(): Promise<ReportRead[]> {
  return apiFetch<ReportRead[]>("/reports");
}

export function fetchReportById(id: number): Promise<ReportRead> {
  return apiFetch<ReportRead>(`/reports/${id}`);
}

export function createReport(data: ReportCreate): Promise<ReportRead> {
  return apiFetch<ReportRead>("/reports", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function addComment(reportId: number, content: string): Promise<CommentRead> {
  return apiFetch<CommentRead>(`/reports/${reportId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}
