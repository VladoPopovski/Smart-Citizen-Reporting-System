import { AppLayout } from "@/components/AppLayout";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, Calendar, Eye } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchReports, updateReportPriority, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, formatCoords, deriveTitle, getStatusStyle, getPriorityLabel, getPriorityStyle } from "@/lib/reportHelpers";
import { useToast } from "@/hooks/use-toast";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function AssignedComplaintsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel } = useLookups();
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: reports = [] } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const priorityMutation = useMutation({
    mutationFn: ({ reportId, priority }: { reportId: number; priority: PriorityValue }) =>
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

  const assigned = reports.filter((r) => r.status_id === 1 || r.status_id === 2);
  const filtered =
    statusFilter === "all"
      ? assigned
      : assigned.filter((r) => String(r.status_id) === statusFilter);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Доделени пријави</h1>
            <p className="text-muted-foreground text-sm">Пријави доделени на вас за преглед и решавање.</p>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Сите</SelectItem>
              <SelectItem value="1">Нова</SelectItem>
              <SelectItem value="2">Во тек</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          {filtered.map((r) => (
            <Card key={r.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="py-4 flex items-center justify-between">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm text-muted-foreground">#{r.id}</span>
                    <h3 className="font-semibold text-foreground">{deriveTitle(r.description)}</h3>
                    <Badge variant="outline" className={getStatusStyle(r.status_id)}>
                      {statusLabel(r.status_id)}
                    </Badge>
                    <Badge variant="secondary">{categoryLabel(r.category_id)}</Badge>
                    <Badge variant="outline" className={getPriorityStyle(r.priority)}>
                      {getPriorityLabel(r.priority)}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    {r.latitude != null && r.longitude != null && (
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{formatCoords(r.latitude, r.longitude)}</span>
                    )}
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(r.created_at)}</span>
                    <span>корисник {r.user_id.slice(0, 8)}...</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Select
                    value={r.priority ?? undefined}
                    onValueChange={(value) => {
                      const nextPriority = value as PriorityValue;
                      if (nextPriority === r.priority) return;
                      priorityMutation.mutate({ reportId: r.id, priority: nextPriority });
                    }}
                    disabled={priorityMutation.isPending}
                  >
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Приоритет" />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((option) => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="outline" size="sm" onClick={() => navigate(`/complaints/${r.id}`)}>
                    <Eye className="mr-1 h-3.5 w-3.5" /> Преглед
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            Нема доделени пријави со избраниот филтер.
          </div>
        )}
      </div>
    </AppLayout>
  );
}
