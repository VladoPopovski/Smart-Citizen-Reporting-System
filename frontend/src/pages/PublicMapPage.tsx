import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchReports, type ReportRead } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Map as MapIcon, Filter, Loader2, Plus } from "lucide-react";
import { useRole } from "@/context/RoleContext";

// Fix default marker icon
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const getMarkerColorForPriority = (priority: string | null | undefined) => {
  if (!priority) return "#64748b";
  const p = priority.trim().toLowerCase();
  if (p.includes("итен") || p.includes("urgent") || p.includes("critical")) return "#ef4444"; // red
  if (p.includes("висок") || p.includes("high")) return "#eab308"; // amber
  if (p.includes("среден") || p.includes("medium") || p.includes("normal")) return "#3b82f6"; // blue
  if (p.includes("низок") || p.includes("low")) return "#22c55e"; // green
  return "#64748b";
};

const getMarkerIconByPriority = (priority: string | null | undefined) => {
  const color = getMarkerColorForPriority(priority);
  return new L.DivIcon({
    className: "custom-div-icon",
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
};

export default function PublicMapPage() {
  const navigate = useNavigate();
  const { role } = useRole();
  const { categories, statuses, categoryLabel, statusLabel } = useLookups();
  const statusOptions = statuses.filter((s) => {
    const n = s.name.trim().toLowerCase();
    return n.includes("активен") || n.includes("решен");
  });
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports", "all-public"],
    queryFn: fetchReports, // In a real app, this might be a dedicated public endpoint
  });

  const filteredReports = reports.filter((r) => {
    if (r.latitude == null || r.longitude == null) return false;
    const matchStatus = statusFilter === "all" || String(r.status_id) === statusFilter;
    const matchCategory = categoryFilter === "all" || String(r.category_id) === categoryFilter;
    return matchStatus && matchCategory;
  });

  return (
      <div className="h-[calc(100vh-8rem)] flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <MapIcon className="h-6 w-6 text-primary" /> Интерактивна мапа
            </h1>
            <p className="text-sm text-muted-foreground">Преглед на сите пријавени проблеми во градот.</p>
          </div>
          
          <Card className="w-full sm:w-auto">
            <CardContent className="p-2 flex flex-wrap gap-2 items-center">
              <Filter className="h-4 w-4 text-muted-foreground ml-2" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px] h-9 text-xs"><SelectValue placeholder="Статус" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Сите статуси</SelectItem>
                  {statusOptions.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[160px] h-9 text-xs"><SelectValue placeholder="Категорија" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Сите категории</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>{getCategoryMacedonianName(c.name)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        </div>

        <div className="flex-1 rounded-xl overflow-hidden border border-border relative z-0">
          {isLoading && (
            <div className="absolute inset-0 bg-background/50 backdrop-blur-[2px] z-[1001] flex flex-col items-center justify-center gap-2">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
              <p className="text-sm font-medium">Се вчитува мапата...</p>
            </div>
          )}

          {!isLoading && filteredReports.length === 0 && (
            <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 z-[1001] flex justify-center px-4">
              <div className="bg-background/90 backdrop-blur-sm p-6 rounded-xl border shadow-xl text-center space-y-4 max-w-sm">
                <div className="bg-muted w-12 h-12 rounded-full flex items-center justify-center mx-auto">
                  <MapIcon className="h-6 w-6 text-muted-foreground" />
                </div>
                <div className="space-y-1">
                  <p className="font-medium text-foreground">Не се пронајдени пријави на мапата.</p>
                  <p className="text-xs text-muted-foreground">
                    Пробајте да ги промените филтрите{role === "citizen" && ' или бидете првиот што ќе поднесе нов проблем.'}
                  </p>
                </div>
                {role === "citizen" && (
                  <Button size="sm" onClick={() => navigate("/new-complaint")} className="w-full">
                    <Plus className="mr-2 h-4 w-4" /> Пријави проблем
                  </Button>
                )}
              </div>
            </div>
          )}

          <MapContainer center={[41.9981, 21.4254]} zoom={13} style={{ height: "100%", width: "100%" }} aria-label="Интерактивна мапа со пријави">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filteredReports.map((r) => (
              <Marker 
                key={r.id} 
                position={[r.latitude!, r.longitude!]} 
                icon={getMarkerIconByPriority(r.priority)}
                aria-label={`Локација: ${deriveTitle(r.description)}`}
              >
                <Popup className="custom-popup">
                  <div className="p-1 space-y-2 min-w-[200px]">
                    <div className="flex justify-between items-start gap-2">
                      <h3 className="font-bold text-sm leading-tight">{deriveTitle(r.description)}</h3>
                      <Badge className={`${getStatusStyle(statusLabel(r.status_id))} text-[10px] px-1.5 py-0 h-4`}>
                        {statusLabel(r.status_id)}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">{r.description}</p>
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
                      {categoryLabel(r.category_id)}
                    </Badge>
                    <div className="flex items-center justify-start">
                      <Badge variant="outline" className={`${getPriorityStyle(r.priority)} text-[10px] px-1.5 py-0 h-4`}>
                        {getPriorityLabel(r.priority)}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center pt-1">
                      <span className="text-[10px] text-muted-foreground">{formatDate(r.created_at)}</span>
                      <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => navigate(`/complaints/${r.id}`)}>
                        Детали
                      </Button>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
          
          <div className="absolute bottom-4 left-4 bg-background/90 backdrop-blur-sm p-3 rounded-lg border border-border shadow-lg z-[1000] text-xs space-y-2">
            <p className="font-semibold border-bottom pb-1 mb-1">Легенда(Приоритет):</p>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444', border: '1px solid white' }} /> Итен</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308', border: '1px solid white' }} /> Висок</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6', border: '1px solid white' }} /> Среден</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#22c55e', border: '1px solid white' }} /> Низок</div>
          </div>
        </div>
      </div>
  );
}
