import { AppLayout } from "@/components/AppLayout";
import { complaints } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, MoreHorizontal } from "lucide-react";
import { useState } from "react";

const statusStyles: Record<string, string> = {
  new: "bg-info/10 text-info",
  in_progress: "bg-warning/10 text-warning",
  resolved: "bg-success/10 text-success",
  rejected: "bg-destructive/10 text-destructive",
  pending: "bg-muted text-muted-foreground",
};

const statusLabels: Record<string, string> = {
  new: "Нова",
  in_progress: "Во тек",
  pending: "Во чекање",
  resolved: "Решено",
  rejected: "Одбиено",
};

const priorityLabels: Record<string, string> = {
  high: "Високо",
  medium: "Средно",
  low: "Ниско",
};

export default function ManageComplaintsPage() {
  const [search, setSearch] = useState("");

  const filtered = complaints.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) || c.citizen.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Управување со пријави</h1>
          <p className="text-muted-foreground text-sm">Прегледајте и управувајте со сите пријави во системот.</p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle>Сите пријави</CardTitle>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Пребарај пријави..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="text-left py-3 px-2 font-medium">ID</th>
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
                  {filtered.map((c) => (
                    <tr key={c.id} className="border-b last:border-0 hover:bg-secondary/50 transition-colors">
                      <td className="py-3 px-2 font-mono text-muted-foreground">{c.id}</td>
                      <td className="py-3 px-2 font-medium text-foreground">{c.title}</td>
                      <td className="py-3 px-2 text-muted-foreground">{c.citizen}</td>
                      <td className="py-3 px-2 text-muted-foreground">{c.category}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className={statusStyles[c.status]}>
                          {statusLabels[c.status]}
                        </Badge>
                      </td>
                      <td className="py-3 px-2">
                        <span className={`text-xs font-medium ${
                          c.priority === "high" ? "text-destructive" :
                          c.priority === "medium" ? "text-warning" : "text-success"
                        }`}>
                          {priorityLabels[c.priority]}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">{c.date}</td>
                      <td className="py-3 px-2">
                        <Button variant="ghost" size="sm"><MoreHorizontal className="h-4 w-4" /></Button>
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
