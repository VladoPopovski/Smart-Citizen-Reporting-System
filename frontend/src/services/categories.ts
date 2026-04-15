import { apiFetch } from "./api";

export interface Category {
  id: number;
  name: string;
}

export function fetchCategories(): Promise<Category[]> {
  return apiFetch<Category[]>("/categories/");
}
