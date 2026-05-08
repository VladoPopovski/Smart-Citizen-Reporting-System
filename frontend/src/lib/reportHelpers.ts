export function getStatusStyle(statusName: string | null | undefined): string {
  const n = (statusName ?? "").trim().toLowerCase();
  if (RESOLVED_STATUS_NAMES.has(n)) return "bg-success/10 text-success border-success/20";
  if (ACTIVE_STATUS_NAMES.has(n))   return "bg-info/10 text-info border-info/20";
  return "bg-muted text-muted-foreground";
}

export function deriveTitle(description: string, maxLen = 50): string {
  if (description.length <= maxLen) return description;
  const cut = description.substring(0, maxLen);
  const lastSpace = cut.lastIndexOf(" ");
  return (lastSpace > 20 ? cut.substring(0, lastSpace) : cut) + "…";
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("mk-MK", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatCoords(lat: number, lng: number): string {
  return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

function normalizePriority(priority: string | null | undefined): string {
  if (!priority || typeof priority !== "string") return "";
  return priority.trim().toLowerCase();
}

export function getPriorityLabel(priority: string | null | undefined): string {
  const normalized = normalizePriority(priority);
  if (normalized === "итен" || normalized === "urgent" || normalized === "critical") return "Итен";
  if (normalized === "висок" || normalized === "high") return "Висок";
  if (normalized === "среден" || normalized === "medium" || normalized === "normal") return "Среден";
  if (normalized === "низок" || normalized === "low") return "Низок";
  return "Непознат";
}

export function getPriorityStyle(priority: string | null | undefined): string {
  const normalized = normalizePriority(priority);
  if (normalized === "итен" || normalized === "urgent" || normalized === "critical") {
    return "bg-destructive/10 text-destructive border-destructive/20";
  }
  if (normalized === "висок" || normalized === "high") {
    return "bg-warning/10 text-warning border-warning/20";
  }
  if (normalized === "среден" || normalized === "medium" || normalized === "normal") {
    return "bg-info/10 text-info border-info/20";
  }
  if (normalized === "низок" || normalized === "low") {
    return "bg-success/10 text-success border-success/20";
  }
  return "bg-muted text-muted-foreground";
}

export const CATEGORY_TRANSLATIONS: Record<string, string> = {
  Environment: "Околина",
  Infrastructure: "Инфраструктура",
  Safety: "Безбедност",
  Other: "Друго",
};

export function getCategoryMacedonianName(categoryName: string): string {
  return CATEGORY_TRANSLATIONS[categoryName] || categoryName;
}

const ACTIVE_STATUS_NAMES = new Set([
  "active",
  "aktiven",
  "aktivna",
  "aktivni",
  "активен",
  "активна",
  "активно",
  "активни",
  "submitted",
  "in progress",
  "pending",
  "нов",
  "нова",
  "поднесен",
  "поднесена",
  "во тек",
  "на чекање",
]);

const RESOLVED_STATUS_NAMES = new Set([
  "resolved",
  "closed",
  "resen",
  "reshen",
  "решен",
  "решена",
  "решено",
  "решени",
  "затворен",
  "затворена",
  "затворено",
  "затворени",
]);

const ADMIN_OFFICER_STATUS_OPTION_NAMES = new Set([
  "aktiven",
  "активен",
  "Ð°ÐºÑ‚Ð¸Ð²ÐµÐ½",
  "resen",
  "reshen",
  "решен",
  "Ñ€ÐµÑˆÐµÐ½",
]);

function normalizeStatusName(status: string): string {
  return status.trim().toLowerCase().replace(/[_-]/g, " ").replace(/\s+/g, " ");
}

export function isActiveStatus(status: string): boolean {
  return ACTIVE_STATUS_NAMES.has(normalizeStatusName(status));
}

export function isResolvedStatus(status: string): boolean {
  return RESOLVED_STATUS_NAMES.has(normalizeStatusName(status));
}

export function isAdminOfficerStatusOption(status: string): boolean {
  return ADMIN_OFFICER_STATUS_OPTION_NAMES.has(normalizeStatusName(status));
}
