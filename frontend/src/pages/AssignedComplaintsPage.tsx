import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, Calendar, FileText, Map as MapIcon } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchReports, updateReportPriority, updateReportStatus, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, formatCoords, deriveTitle, getStatusStyle, isAdminOfficerStatusOption, getPriorityLabel, getPriorityStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { useRole } from "@/context/RoleContext";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

const PRIORITY_ORDER: Record<string, number> = { "Итен": 0, "Висок": 1, "Среден": 2, "Низок": 3 };

const PRIORITY_BORDER: Record<string, string> = {
  "Итен":   "border-l-4 border-l-red-500",
  "Висок":  "border-l-4 border-l-orange-400",
  "Среден": "border-l-4 border-l-yellow-400",
  "Низок":  "border-l-4 border-l-slate-300",
};

export default function AssignedComplaintsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel, statuses, categories } = useLookups();
  const { role } = useRole();
  const statusOptions = (role === "officer" || role === "admin")
    ? statuses.filter((s) => isAdminOfficerStatusOption(s.name))
    : statuses;


  const [priorityFilter, setPriorityFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"priority" | "date">("priority");

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const priorityMutation = useMutation({
    mutationFn: ({ reportId, priority }: { reportId: string; priority: PriorityValue }) =>
      updateReportPriority(reportId, priority),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Приоритетот е ажуриран." });
    },
    onError: (err: Error) => {
      toast({ title: "Грешка", description: err.message ?? "Неуспешно ажурирање на приоритет.", variant: "destructive" });
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ reportId, status_id }: { reportId: string; status_id: number }) =>
      updateReportStatus(reportId, status_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Статусот е ажуриран." });
    },
    onError: (err: Error) => {
      toast({ title: "Грешка", description: err.message ?? "Неуспешно ажурирање на статус.", variant: "destructive" });
    },
  });

  const counts = {
    "Итен":   reports.filter((r) => r.priority === "Итен").length,
    "Висок":  reports.filter((r) => r.priority === "Висок").length,
    "Среден": reports.filter((r) => r.priority === "Среден").length,
    "Низок":  reports.filter((r) => r.priority === "Низок").length,
  };

  const filtered = reports
    .filter((r) => priorityFilter === "all" || r.priority === priorityFilter)
    .filter((r) => categoryFilter === "all" || r.category_id?.toString() === categoryFilter);

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "priority") {
      const pa = PRIORITY_ORDER[a.priority ?? ""] ?? 99;
      const pb = PRIORITY_ORDER[b.priority ?? ""] ?? 99;
      if (pa !== pb) return pa - pb;
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Доделени пријави</h1>
        <p className="text-muted-foreground text-sm">Пријави доделени на вас за преглед и решавање.</p>
      </div>

      {/* Priority summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {(["Итен", "Висок", "Среден", "Низок"] as const).map((p) => (
          <Card
            key={p}
            className={`cursor-pointer transition-opacity ${PRIORITY_BORDER[p]} ${priorityFilter !== "all" && priorityFilter !== p ? "opacity-40" : ""}`}
            onClick={() => setPriorityFilter(priorityFilter === p ? "all" : p)}
          >
            <CardContent className="py-3 px-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">{p}</p>
              <p className="text-2xl font-bold">{isLoading ? "—" : counts[p]}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-2">
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-40" aria-label="Филтрирај по приоритет"><SelectValue placeholder="Приоритет" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Сите приоритети</SelectItem>
            {PRIORITY_OPTIONS.slice().reverse().map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-44" aria-label="Филтрирај по категорија"><SelectValue placeholder="Категорија" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Сите категории</SelectItem>
            {categories.map((c) => (
              <SelectItem key={c.id} value={c.id.toString()}>{getCategoryMacedonianName(c.name)}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex gap-1 ml-auto">
          <Button
            variant={sortBy === "priority" ? "secondary" : "outline"}
            size="sm"
            className="text-xs h-9"
            onClick={() => setSortBy("priority")}
          >
            По приоритет
          </Button>
          <Button
            variant={sortBy === "date" ? "secondary" : "outline"}
            size="sm"
            className="text-xs h-9"
            onClick={() => setSortBy("date")}
          >
            По датум
          </Button>
        </div>
      </div>

      {/* Report count */}
      {!isLoading && (
        <p className="text-xs text-muted-foreground">
          {sorted.length} {sorted.length === 1 ? "пријава" : "пријави"}
        </p>
      )}

      {/* List */}
      <div className="space-y-3" aria-live="polite">
        {isLoading && Array.from({ length: 4 }).map((_, idx) => (
          <Card key={`skeleton-${idx}`}>
            <CardContent className="py-4 space-y-3">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-4 w-1/3" />
              <div className="flex gap-2"><Skeleton className="h-8 w-24" /><Skeleton className="h-8 w-24" /></div>
            </CardContent>
          </Card>
        ))}

        {!isLoading && sorted.map((r) => {
          const username = r.user_email ? r.user_email.split("@")[0] : r.user_id.slice(0, 8);
          return (
            <Card
              key={r.id}
              className={`hover:shadow-sm transition-shadow cursor-pointer ${PRIORITY_BORDER[r.priority ?? ""] ?? "border-l-4 border-l-slate-200"}`}
              onClick={() => navigate(`/complaints/${r.id}`)}
              role="link"
              aria-label={`Пријава: ${deriveTitle(r.description)}`}
            >
              <CardContent className="py-4 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground truncate">{deriveTitle(r.description)}</h3>
                    <Badge variant="outline" className={`${getStatusStyle(statusLabel(r.status_id))} flex-shrink-0`}>
                      {statusLabel(r.status_id)}
                    </Badge>
                    <Badge variant="secondary" className="flex-shrink-0 text-[10px]">{categoryLabel(r.category_id)}</Badge>
                    <Badge variant="outline" className={`${getPriorityStyle(r.priority)} flex-shrink-0 text-[10px]`}>
                      {getPriorityLabel(r.priority)}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                  {r.latitude != null && r.longitude != null && (
                    <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{formatCoords(r.latitude, r.longitude)}</span>
                  )}
                  <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(r.created_at)}</span>
                  <span>корисник {username}</span>
                </div>
                <div className="flex items-center gap-2 flex-wrap" onClick={(e) => e.stopPropagation()}>
                  <Select
                    value={r.priority ?? undefined}
                    onValueChange={(value) => {
                      const next = value as PriorityValue;
                      if (next === r.priority) return;
                      priorityMutation.mutate({ reportId: r.id, priority: next });
                    }}
                    disabled={priorityMutation.isPending}
                  >
                    <SelectTrigger className="w-[130px] h-8 text-xs" aria-label="Промени приоритет">
                      <SelectValue placeholder="Приоритет" />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  <Select
                    value={r.status_id?.toString() ?? undefined}
                    onValueChange={(value) => {
                      const newId = Number(value);
                      if (newId === r.status_id) return;
                      statusMutation.mutate({ reportId: r.id, status_id: newId });
                    }}
                    disabled={statusMutation.isPending}
                  >
                    <SelectTrigger className="w-[140px] h-8 text-xs" aria-label="Промени статус">
                      <SelectValue placeholder="Статус" />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((s) => (
                        <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {!isLoading && sorted.length === 0 && (
        <div className="text-center py-20 bg-muted/20 rounded-xl border-2 border-dashed space-y-4">
          <div className="bg-background w-12 h-12 rounded-full flex items-center justify-center mx-auto shadow-sm">
            <FileText className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="space-y-1">
            <p className="font-medium text-foreground">Нема пријави.</p>
            <p className="text-sm text-muted-foreground">Нема резултати за избраните филтри.</p>
          </div>
          <Button variant="outline" onClick={() => navigate("/public-map")} className="gap-2">
            <MapIcon className="h-4 w-4" /> Погледни ја мапата
          </Button>
        </div>
      )}
    </div>
  );
}
