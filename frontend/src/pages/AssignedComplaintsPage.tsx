import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, Calendar, FileText, Loader2, Map as MapIcon } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchReports, updateReportPriority, updateReportStatus, updateReportCategory, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, formatCoords, deriveTitle, getStatusStyle, isActiveStatus, isAdminOfficerStatusOption, getPriorityLabel, getPriorityStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { useRole } from "@/context/RoleContext";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function AssignedComplaintsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel, statuses, categories } = useLookups();
  const { role } = useRole();
  const statusOptions = (role === "officer" || role === "admin")
    ? statuses.filter((s) => isAdminOfficerStatusOption(s.name))
    : statuses;
  const [statusFilter, setStatusFilter] = useState("all");

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

  const categoryMutation = useMutation({
    mutationFn: ({ reportId, category_id }: { reportId: string; category_id: number }) =>
      updateReportCategory(reportId, category_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Категоријата е ажурирана." });
    },
    onError: (err: Error) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на категорија.",
        variant: "destructive",
      });
    },
  });

  const filtered =
    statusFilter === "all"
      ? reports
      : reports.filter((r) => statusLabel(r.status_id) === statusFilter);

  return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Доделени пријави</h1>
            <p className="text-muted-foreground text-sm">Пријави доделени на вас за преглед и решавање.</p>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40" aria-label="Филтрирај по статус"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Сите</SelectItem>
              <SelectItem value="Активен">Активен</SelectItem>
            </SelectContent>
          </Select>
        </div>

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

          {!isLoading && filtered.map((r) => {
            const username = r.user_email ? r.user_email.split("@")[0] : r.user_id.slice(0, 8);
            return (
              <Card
                key={r.id}
                className="hover:shadow-sm transition-shadow cursor-pointer"
                onClick={() => navigate(`/complaints/${r.id}`)}
                role="link"
                aria-label={`Пријава: ${deriveTitle(r.description)}`}
              >
                <CardContent className="py-4 space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <h3 className="font-semibold text-foreground truncate group-hover:text-primary transition-colors">{deriveTitle(r.description)}</h3>
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
                      const nextPriority = value as PriorityValue;
                      if (nextPriority === r.priority) return;
                      priorityMutation.mutate({ reportId: r.id, priority: nextPriority });
                    }}
                    disabled={priorityMutation.isPending}
                  >
                    <SelectTrigger className="w-[130px] h-8 text-xs" aria-label="Промени приоритет">
                      <SelectValue placeholder="Приоритет" />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((option) => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={r.status_id?.toString() ?? undefined}
                    onValueChange={(value) => {
                      const newStatusId = Number(value);
                      if (newStatusId === r.status_id) return;
                      statusMutation.mutate({ reportId: r.id, status_id: newStatusId });
                    }}
                    disabled={statusMutation.isPending}
                  >
                    <SelectTrigger className="w-[140px] h-8 text-xs" aria-label="Промени статус">
                      <SelectValue placeholder="Статус" />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((s) => (
                        <SelectItem key={s.id} value={s.id.toString()}>
                          {s.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {!isLoading && filtered.length === 0 && (
          <div className="text-center py-20 bg-muted/20 rounded-xl border-2 border-dashed space-y-4">
            <div className="bg-background w-12 h-12 rounded-full flex items-center justify-center mx-auto shadow-sm">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <p className="font-medium text-foreground">Нема доделени пријави.</p>
              <p className="text-sm text-muted-foreground">Сите ваши пријави се решени или немате доделени нови.</p>
            </div>
            <Button variant="outline" onClick={() => navigate("/public-map")} className="gap-2">
              <MapIcon className="h-4 w-4" /> Погледни ја мапата
            </Button>
          </div>
        )}
      </div>

  );
}
