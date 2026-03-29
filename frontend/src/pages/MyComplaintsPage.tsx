import { useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { complaints } from "@/data/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, Plus, MapPin, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";

const statusStyles: Record<string, string> = {
  new: "bg-info/10 text-info border-info/20",
  in_progress: "bg-warning/10 text-warning border-warning/20",
  pending: "bg-muted text-muted-foreground",
  resolved: "bg-success/10 text-success border-success/20",
  rejected: "bg-destructive/10 text-destructive border-destructive/20",
};

const statusLabels: Record<string, string> = {
  new: "Нова",
  in_progress: "Во тек",
  pending: "Во чекање",
  resolved: "Решено",
  rejected: "Одбиено",
};

export default function MyComplaintsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const filtered = complaints.filter((c) => {
    const matchSearch = c.title.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || c.status === statusFilter;
    const matchCategory = categoryFilter === "all" || c.category === categoryFilter;
    return matchSearch && matchStatus && matchCategory;
  });

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Мои пријави</h1>
            <p className="text-muted-foreground text-sm">Прегледајте го статусот и историјата на вашите поднесени проблеми.</p>
          </div>
          <Button onClick={() => navigate("/new-complaint")}>
            <Plus className="mr-2 h-4 w-4" /> Нова пријава
          </Button>
        </div>

        <Card>
          <CardContent className="py-3 flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Пребарај по наслов или опис..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40"><SelectValue placeholder="Статус" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Сите статуси</SelectItem>
                <SelectItem value="new">Нова</SelectItem>
                <SelectItem value="in_progress">Во тек</SelectItem>
                <SelectItem value="resolved">Решено</SelectItem>
                <SelectItem value="rejected">Одбиено</SelectItem>
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-44"><SelectValue placeholder="Категорија" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Сите категории</SelectItem>
                <SelectItem value="Инфраструктура">Инфраструктура</SelectItem>
                <SelectItem value="Комунални услуги">Комунални услуги</SelectItem>
                <SelectItem value="Администрација">Администрација</SelectItem>
                <SelectItem value="Безбедност">Безбедност</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((c) => (
            <Card key={c.id} className="hover:shadow-md transition-shadow cursor-pointer group">
              <CardContent className="p-5 space-y-3">
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">{c.title}</h3>
                  <Badge variant="outline" className={statusStyles[c.status]}>
                    {statusLabels[c.status]}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">{c.description}</p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{c.location}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1 text-xs text-muted-foreground"><Calendar className="h-3 w-3" />{c.date}</span>
                  <Badge variant="secondary" className="text-xs">{c.category}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            Не се пронајдени пријави со вашите филтри.
          </div>
        )}

        <p className="text-sm text-muted-foreground">Прикажани {filtered.length} од {complaints.length} пријави</p>
      </div>
    </AppLayout>
  );
}
