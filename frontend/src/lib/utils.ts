import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getLocalPartFromEmail(email?: string | null): string | undefined {
  if (!email) return undefined;
  const parts = String(email).split("@");
  if (parts.length === 0) return undefined;
  const local = parts[0].trim();
  return local === "" ? undefined : local;
}
