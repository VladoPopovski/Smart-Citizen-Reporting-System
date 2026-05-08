import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Clock, CheckCircle, AlertTriangle, ClipboardList } from "lucide-react";
import { useRole } from "@/context/RoleContext";
import { isActiveStatus, isAdminOfficerStatusOption, isResolvedStatus } from "@/lib/reportHelpers";
import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchReports, updateReportStatus, updateReportCategory } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, deriveTitle, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useNavigate } from "react-router-dom";
import { getLocalPartFromEmail } from "@/lib/utils";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { role, userId, userName, userEmail } = useRole();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: reports = [], isLoading, error } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });
  const { statusLabel, categoryLabel, statuses, categories } = useLookups();
  const statusOptions = (role === "officer" || role === "admin")
    ? statuses.filter((s) => isAdminOfficerStatusOption(s.name))
    : statuses;

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

  const stats = useMemo(() => {
    const active = reports.filter((r) => isActiveStatus(statusLabel(r.status_id))).length;

    const resolved = reports.filter((r) => isResolvedStatus(statusLabel(r.status_id))).length;

    const urgent = reports.filter((r) => getPriorityLabel(r.priority) === "Итен").length;

    return {
      total: reports.length,
      active,
      resolved,
      urgent,
    };
  }, [reports, statusLabel]);

  const recentReports = [...reports]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10);

  const statCards = [
    { label: "Вкупно пријави", value: stats.total, icon: FileText, color: "text-primary" },
    { label: "Активни (во тек)", value: stats.active, icon: Clock, color: "text-warning" },
    { label: "Решени", value: stats.resolved, icon: CheckCircle, color: "text-success" },
    { label: "Итни случаи", value: stats.urgent, icon: AlertTriangle, color: "text-destructive" },
  ];

  return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Контролна табла</h1>
          <p className="text-muted-foreground text-sm">
            Преглед, приоритизација и ефикасно решавање на граѓански пријави во реално време.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {isLoading && Array.from({ length: 4 }).map((_, idx) => (
            <Card key={`skeleton-${idx}`}>
              <CardContent className="py-5">
                <Skeleton className="h-4 w-2/3 mb-2" />
                <Skeleton className="h-8 w-1/3" />
              </CardContent>
            </Card>
          ))}
          {!isLoading && statCards.map((s) => (
            <Card key={s.label}>
              <CardContent className="py-5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="text-2xl font-bold text-foreground">{s.value.toLocaleString()}</p>
                </div>
                <s.icon className={`h-8 w-8 ${s.color} opacity-70`} />
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Последни пријави</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="text-left py-3 px-2 font-medium">Наслов</th>
                    <th className="text-left py-3 px-2 font-medium">Категорија</th>
                    <th className="text-left py-3 px-2 font-medium">Статус</th>
                    <th className="text-left py-3 px-2 font-medium">Датум</th>
                    <th className="text-left py-3 px-2 font-medium">Приоритет</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading && Array.from({ length: 5 }).map((_, idx) => (
                    <tr key={`skeleton-row-${idx}`} className="border-b last:border-0">
                      <td className="py-3 px-2"><Skeleton className="h-5 w-48 mb-1" /><Skeleton className="h-3 w-24" /></td>
                      <td className="py-3 px-2"><Skeleton className="h-8 w-[140px]" /></td>
                      <td className="py-3 px-2"><Skeleton className="h-8 w-[140px]" /></td>
                      <td className="py-3 px-2"><Skeleton className="h-4 w-24" /></td>
                      <td className="py-3 px-2"><Skeleton className="h-6 w-16" /></td>
                    </tr>
                  ))}
                  {!isLoading && recentReports.map((report) => {
                    let mkCategory = getCategoryMacedonianName(categoryLabel(report.category_id));
                    return (
                      <tr
                        key={report.id}
                        className="border-b last:border-0 hover:bg-secondary/50 transition-colors cursor-pointer"
                        onClick={() => navigate(`/complaints/${report.id}`)}
                        role="link"
                        aria-label={`Пријава: ${deriveTitle(report.description)}`}
                      >
                        <td className="py-3 px-2">
                          <div className="font-medium text-foreground">{deriveTitle(report.description, 64)}</div>
                          <div className="text-xs text-muted-foreground">корисник {getLocalPartFromEmail(report.user_email ?? (report.user_id === userId ? userEmail : undefined)) ?? (report.user_id ? `${String(report.user_id).slice(0,8)}...` : "—")}</div>
                        </td>
                        <td className="py-3 px-2" onClick={(e) => e.stopPropagation()}>
                          <Select
                            value={report.category_id?.toString() ?? undefined}
                            onValueChange={(value) => {
                              const newCategoryId = Number(value);
                              if (newCategoryId === report.category_id) return;
                              categoryMutation.mutate({ reportId: report.id, category_id: newCategoryId });
                            }}
                            disabled={categoryMutation.isPending}
                          >
                            <SelectTrigger className="w-[140px] text-xs" aria-label="Промени категорија">
                              <SelectValue placeholder="Избери категорија" />
                            </SelectTrigger>
                            <SelectContent>
                              {categories.map((cat) => (
                                <SelectItem key={cat.id} value={cat.id.toString()}>
                                  {getCategoryMacedonianName(cat.name)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="py-3 px-2" onClick={(e) => e.stopPropagation()}>
                          <Select
                            value={report.status_id?.toString() ?? undefined}
                            onValueChange={(value) => {
                              const newStatusId = Number(value);
                              if (newStatusId === report.status_id) return;
                              statusMutation.mutate({ reportId: report.id, status_id: newStatusId });
                            }}
                            disabled={statusMutation.isPending}
                          >
                            <SelectTrigger className="w-[140px] text-xs" aria-label="Промени статус">
                              <SelectValue placeholder="Избери статус" />
                            </SelectTrigger>
                            <SelectContent>
                              {statusOptions.map((s) => (
                                <SelectItem key={s.id} value={s.id.toString()}>
                                  {s.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="py-3 px-2 text-muted-foreground">{formatDate(report.created_at)}</td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className={getPriorityStyle(report.priority)}>
                            {getPriorityLabel(report.priority)}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                  {!isLoading && !error && recentReports.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-20 text-center">
                        <div className="space-y-4">
                           <div className="bg-muted w-12 h-12 rounded-full flex items-center justify-center mx-auto">
                              <FileText className="h-6 w-6 text-muted-foreground" />
                           </div>
                           <div className="space-y-1">
                              <p className="font-medium text-foreground">Нема нови пријави.</p>
                              <p className="text-sm text-muted-foreground">Сите пријави се решени или нема поднесено нови.</p>
                           </div>
                           <Button
                             variant="outline"
                             size="sm"
                             className="gap-2"
                             onClick={() => navigate(role === "admin" ? "/manage-complaints" : "/assigned-complaints")}
                           >
                             <ClipboardList className="h-4 w-4" /> Прегледај ги пријавите
                           </Button>
                        </div>
                      </td>
                    </tr>
                  )}
                  {!isLoading && error && (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-destructive">
                         Неуспешно вчитување на пријавите.
                         <Button variant="link" size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ["reports"] })}>Обиди се повторно</Button>
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
