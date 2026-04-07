import { AppLayout } from "@/components/AppLayout";
import { dashboardStats, complaints } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { useRole } from "@/context/RoleContext";

const statusLabels: Record<string, string> = {
  new: "Нова",
  in_progress: "Во тек",
  resolved: "Решено",
  rejected: "Одбиено",
};

const statusStyles: Record<string, string> = {
  new: "bg-info/10 text-info",
  in_progress: "bg-warning/10 text-warning",
  resolved: "bg-success/10 text-success",
  rejected: "bg-destructive/10 text-destructive",
};

const priorityLabels: Record<string, string> = {
  high: "Високо",
  medium: "Средно",
  low: "Ниско",
};

export default function DashboardPage() {
  const { role } = useRole();

  const statCards = [
    { label: "Вкупно пријави", value: dashboardStats.totalComplaints, icon: FileText, color: "text-primary" },
    { label: "Активни (во тек)", value: dashboardStats.activeComplaints, icon: Clock, color: "text-warning" },
    { label: "Решени (овој месец)", value: dashboardStats.resolvedThisMonth, icon: CheckCircle, color: "text-success" },
    { label: "Итни случаи", value: dashboardStats.urgentCases, icon: AlertTriangle, color: "text-destructive" },
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
          {statCards.map((s) => (
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
                  {complaints.map((c) => (
                    <tr key={c.id} className="border-b last:border-0 hover:bg-secondary/50 transition-colors">
                      <td className="py-3 px-2 font-mono text-muted-foreground">{c.id}</td>
                      <td className="py-3 px-2">
                        <div className="font-medium text-foreground">{c.title}</div>
                        <div className="text-xs text-muted-foreground">од {c.citizen}</div>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">{c.category}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className={statusStyles[c.status]}>
                          {statusLabels[c.status] || c.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">{c.date}</td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium ${
                          c.priority === "high" ? "text-destructive" :
                          c.priority === "medium" ? "text-warning" : "text-success"
                        }`}>
                          <span className={`w-2 h-2 rounded-full ${
                            c.priority === "high" ? "bg-destructive" :
                            c.priority === "medium" ? "bg-warning" : "bg-success"
                          }`} />
                          {priorityLabels[c.priority]}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
