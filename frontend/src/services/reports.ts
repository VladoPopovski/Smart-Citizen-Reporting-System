import { apiFetch } from "./api";

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
}

export interface ReportCreate {
  description: string;
  latitude: number | null;
  longitude: number | null;
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
