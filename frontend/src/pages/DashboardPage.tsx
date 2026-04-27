import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchReports } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, deriveTitle, getPriorityLabel } from "@/lib/reportHelpers";
import { Skeleton } from "@/components/ui/skeleton";

const OPEN_STATUS_NAMES = ["submitted", "in progress", "pending"];
const RESOLVED_STATUS_NAMES = ["resolved", "closed"];

export default function DashboardPage() {
  const { data: reports = [], isLoading, error } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });
  const { statusLabel, categoryLabel } = useLookups();

  const stats = useMemo(() => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const active = reports.filter((r) =>
      OPEN_STATUS_NAMES.includes(statusLabel(r.status_id).toLowerCase())
    ).length;

    const resolvedThisMonth = reports.filter((r) => {
      const reportDate = new Date(r.created_at);
      const isResolved = RESOLVED_STATUS_NAMES.includes(statusLabel(r.status_id).toLowerCase());
      return isResolved && reportDate.getMonth() === currentMonth && reportDate.getFullYear() === currentYear;
    }).length;

    const urgent = reports.filter((r) => getPriorityLabel(r.priority) === "Итен").length;

    return {
      total: reports.length,
      active,
      resolvedThisMonth,
      urgent,
    };
  }, [reports, statusLabel]);

  const recentReports = [...reports]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10);

  const statCards = [
    { label: "Вкупно пријави", value: stats.total, icon: FileText, color: "text-primary" },
    { label: "Активни (во тек)", value: stats.active, icon: Clock, color: "text-warning" },
    { label: "Решени (овој месец)", value: stats.resolvedThisMonth, icon: CheckCircle, color: "text-success" },
    { label: "Итни случаи", value: stats.urgent, icon: AlertTriangle, color: "text-destructive" },
  ];

  return (
    <AppLayout>
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
                    <th className="text-left py-3 px-2 font-medium">ID</th>
                    <th className="text-left py-3 px-2 font-medium">Наслов</th>
                    <th className="text-left py-3 px-2 font-medium">Категорија</th>
                    <th className="text-left py-3 px-2 font-medium">Статус</th>
                    <th className="text-left py-3 px-2 font-medium">Датум</th>
                    <th className="text-left py-3 px-2 font-medium">Приоритет</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-muted-foreground">Се вчитуваат пријавите...</td>
                    </tr>
                  )}
                  {!isLoading && recentReports.map((report) => (
                    <tr key={report.id} className="border-b last:border-0 hover:bg-secondary/50 transition-colors">
                      <td className="py-3 px-2 font-mono text-muted-foreground">#{report.id}</td>
                      <td className="py-3 px-2">
                        <div className="font-medium text-foreground">{deriveTitle(report.description, 64)}</div>
                        <div className="text-xs text-muted-foreground">корисник {report.user_id.slice(0, 8)}</div>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">{categoryLabel(report.category_id)}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className="bg-secondary/60 text-foreground">
                          {statusLabel(report.status_id)}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">{formatDate(report.created_at)}</td>
                      <td className="py-3 px-2">
                        <span className="inline-flex items-center gap-1 text-xs font-medium">
                          {getPriorityLabel(report.priority)}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {!isLoading && !error && recentReports.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-muted-foreground">Нема пријави.</td>
                    </tr>
                  )}
                  {!isLoading && error && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-destructive">Неуспешно вчитување на пријавите.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
