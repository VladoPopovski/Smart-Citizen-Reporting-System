import { apiFetch } from "./api";

export interface Status {
  id: number;
  name: string;
}

export function fetchStatuses(): Promise<Status[]> {
  return apiFetch<Status[]>("/statuses/");
}
