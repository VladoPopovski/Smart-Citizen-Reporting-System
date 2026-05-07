import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Eye, FileText, Loader2 } from "lucide-react";
import { useState } from "react";
import { fetchReports, updateReportPriority, updateReportStatus, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName, isAdminOfficerStatusOption } from "@/lib/reportHelpers";
import { useRole } from "@/context/RoleContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function ManageComplaintsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel, statuses, categories } = useLookups();
  const { role } = useRole();
  const statusOptions = (role === "officer" || role === "admin")
    ? statuses.filter((s) => isAdminOfficerStatusOption(s.name))
    : statuses;
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"priority" | "date">("date");

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
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на приоритет.",
        variant: "destructive",
      });
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
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на статус.",
        variant: "destructive",
      });
    },
  });

  const PRIORITY_ORDER: Record<string, number> = { "Итен": 0, "Висок": 1, "Среден": 2, "Низок": 3 };

  const filtered = [...reports]
    .filter((r) =>
      r.description.toLowerCase().includes(search.toLowerCase()) ||
      String(r.id).includes(search.trim()) ||
      (r.priority ?? "").toLowerCase().includes(search.toLowerCase())
    )
    .filter((r) => priorityFilter === "all" || r.priority === priorityFilter)
    .filter((r) => categoryFilter === "all" || r.category_id?.toString() === categoryFilter)
    .sort((a, b) => {
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
        <h1 className="text-2xl font-bold text-foreground">Управување со пријави</h1>
        <p className="text-muted-foreground text-sm">Прегледајте и управувајте со сите пријави во системот.</p>
      </div>

      <Card>
        <CardHeader className="pb-3 space-y-3">
          <div className="flex items-center justify-between">
            <CardTitle>Сите пријави</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Пребарај пријави..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-40 h-8 text-xs" aria-label="Филтрирај по приоритет"><SelectValue placeholder="Приоритет" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Сите приоритети</SelectItem>
                {["Итен", "Висок", "Среден", "Низок"].map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-44 h-8 text-xs" aria-label="Филтрирај по категорија"><SelectValue placeholder="Категорија" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Сите категории</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c.id} value={c.id.toString()}>{getCategoryMacedonianName(c.name)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex gap-1 ml-auto">
              <Button variant={sortBy === "date" ? "secondary" : "outline"} size="sm" className="text-xs h-8" onClick={() => setSortBy("date")}>По датум</Button>
              <Button variant={sortBy === "priority" ? "secondary" : "outline"} size="sm" className="text-xs h-8" onClick={() => setSortBy("priority")}>По приоритет</Button>
            </div>
            {!isLoading && (
              <span className="text-xs text-muted-foreground">{filtered.length} пријави</span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-3 px-2 font-medium">Наслов</th>
                  <th className="text-left py-3 px-2 font-medium">Граѓанин</th>
                  <th className="text-left py-3 px-2 font-medium">Категорија</th>
                  <th className="text-left py-3 px-2 font-medium">Статус</th>
                  <th className="text-left py-3 px-2 font-medium">Приоритет</th>
                  <th className="text-left py-3 px-2 font-medium">Датум</th>
                  <th className="text-left py-3 px-2 font-medium">Акции</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && Array.from({ length: 8 }).map((_, idx) => (
                  <tr key={`skeleton-${idx}`} className="border-b last:border-0">
                    <td className="py-3 px-2"><Skeleton className="h-4 w-40" /></td>
                    <td className="py-3 px-2"><Skeleton className="h-4 w-24" /></td>
                    <td className="py-3 px-2"><Skeleton className="h-4 w-24" /></td>
                    <td className="py-3 px-2"><Skeleton className="h-6 w-20" /></td>
                    <td className="py-3 px-2"><Skeleton className="h-8 w-28" /></td>
                    <td className="py-3 px-2"><Skeleton className="h-4 w-24" /></td>
                    <td className="py-3 px-2"><Skeleton className="h-8 w-8" /></td>
                  </tr>
                ))}
                {!isLoading && filtered.map((r) => {
                  let username = r.user_email ? r.user_email.split("@")[0] : r.user_id?.slice(0, 8);
                  let categoryName = categoryLabel(r.category_id);
                  let mkCategory = getCategoryMacedonianName(categoryName);
                  return (
                    <tr
                      key={r.id}
                      className="border-b last:border-0 hover:bg-secondary/50 transition-colors cursor-pointer"
                      onClick={() => navigate(`/complaints/${r.id}`)}
                      role="link"
                      aria-label={`Пријава: ${deriveTitle(r.description)}`}
                    >
                      <td className="py-3 px-2 font-medium text-foreground">{deriveTitle(r.description)}</td>
                      <td className="py-3 px-2 text-muted-foreground">{username}</td>
                      <td className="py-3 px-2 text-muted-foreground">{mkCategory}</td>
                      <td className="py-3 px-2" onClick={(e) => e.stopPropagation()}>
                        <Select
                          value={r.status_id?.toString() ?? undefined}
                          onValueChange={(value) => {
                            const newStatusId = Number(value);
                            if (newStatusId === r.status_id) return;
                            statusMutation.mutate({ reportId: r.id, status_id: newStatusId });
                          }}
                          disabled={statusMutation.isPending}
                        >
                          <SelectTrigger className={`w-[130px] h-8 text-xs ${getStatusStyle(statusLabel(r.status_id))}`} aria-label="Промени статус">
                            <SelectValue placeholder="Статус" />
                          </SelectTrigger>
                          <SelectContent>
                            {statusOptions.map((s) => (
                              <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="py-3 px-2" onClick={(e) => e.stopPropagation()}>
                        <Select
                          value={r.priority ?? undefined}
                          onValueChange={(value) => {
                            const nextPriority = value as PriorityValue;
                            if (nextPriority === r.priority) return;
                            priorityMutation.mutate({ reportId: r.id, priority: nextPriority });
                          }}
                          disabled={priorityMutation.isPending}
                        >
                          <SelectTrigger className="w-[120px] h-8 text-xs" aria-label="Промени приоритет">
                            <SelectValue placeholder="Приоритет" />
                          </SelectTrigger>
                          <SelectContent>
                            {PRIORITY_OPTIONS.map((option) => (
                              <SelectItem key={option} value={option}>{option}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">{formatDate(r.created_at)}</td>
                      <td className="py-3 px-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/complaints/${r.id}`);
                          }}
                          aria-label="Види детали"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
                {!isLoading && filtered.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-20 text-center">
                      <div className="space-y-4">
                        <div className="bg-muted w-12 h-12 rounded-full flex items-center justify-center mx-auto">
                          <FileText className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="space-y-1">
                          <p className="font-medium text-foreground">Не се пронајдени пријави.</p>
                          <p className="text-sm text-muted-foreground">Пробајте со поинакви филтри или пребарување.</p>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => setSearch("")}>
                          Исчисти го пребарувањето
                        </Button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
