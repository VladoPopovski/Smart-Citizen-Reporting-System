import { AppLayout } from "@/components/AppLayout";
import { complaints } from "@/data/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, Calendar, Eye } from "lucide-react";
import { useState } from "react";

const statusStyles: Record<string, string> = {
  new: "bg-info/10 text-info",
  in_progress: "bg-warning/10 text-warning",
  resolved: "bg-success/10 text-success",
  rejected: "bg-destructive/10 text-destructive",
};

const statusLabels: Record<string, string> = {
  new: "Нова",
  in_progress: "Во тек",
};

export default function AssignedComplaintsPage() {
  const [statusFilter, setStatusFilter] = useState("all");

  const assigned = complaints.filter((c) => c.status === "in_progress" || c.status === "new");
  const filtered = statusFilter === "all" ? assigned : assigned.filter((c) => c.status === statusFilter);

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
              <SelectItem value="new">Нова</SelectItem>
              <SelectItem value="in_progress">Во тек</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          {filtered.map((c) => (
            <Card key={c.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="py-4 flex items-center justify-between">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm text-muted-foreground">{c.id}</span>
                    <h3 className="font-semibold text-foreground">{c.title}</h3>
                    <Badge variant="outline" className={statusStyles[c.status]}>
                      {statusLabels[c.status] || c.status}
                    </Badge>
                    <Badge variant="secondary">{c.category}</Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{c.location}</span>
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{c.date}</span>
                    <span>од {c.citizen}</span>
                  </div>
                </div>
                <Button variant="outline" size="sm"><Eye className="mr-1 h-3.5 w-3.5" /> Преглед</Button>
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
