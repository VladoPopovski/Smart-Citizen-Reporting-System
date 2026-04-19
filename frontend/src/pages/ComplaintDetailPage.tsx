import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronLeft, MapPin, Calendar, Tag, History } from "lucide-react";
import { fetchReportById } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, formatCoords, getStatusStyle } from "@/lib/reportHelpers";
import { StatusTimeline } from "@/components/StatusTimeline";
import { CommentsSection } from "@/components/CommentsSection";

export default function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { categoryLabel, statusLabel } = useLookups();

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["reports", id],
    queryFn: () => fetchReportById(Number(id)),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-32" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card><CardContent className="p-6 space-y-4"><Skeleton className="h-8 w-3/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-full" /></CardContent></Card>
            </div>
            <div className="space-y-6">
              <Card><CardContent className="p-6 space-y-4"><Skeleton className="h-6 w-1/2" /><Skeleton className="h-20 w-full" /></CardContent></Card>
            </div>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (error || !report) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-destructive font-semibold">Грешка при вчитување на пријавата.</p>
          <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>Назад</Button>
        </div>
      </AppLayout>
    );
  }

  const historyEntries = report.history_entries
    .filter((h) => h.status_id !== null)
    .map((h) => ({
      id: h.id,
      status_id: h.status_id as number,
      created_at: h.created_at,
    }));

  return (
    <AppLayout>
      <div className="space-y-6">
        <Button variant="ghost" className="pl-0 hover:bg-transparent" onClick={() => navigate(-1)}>
          <ChevronLeft className="mr-2 h-4 w-4" /> Назад
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl">{deriveTitle(report.description)}</CardTitle>
                    <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> {formatDate(report.created_at)}</span>
                      {report.latitude && report.longitude && (
                        <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {formatCoords(report.latitude, report.longitude)}</span>
                      )}
                    </div>
                  </div>
                  <Badge className={getStatusStyle(report.status_id)}>{statusLabel(report.status_id)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-2">Опис</h4>
                  <p className="text-foreground whitespace-pre-wrap">{report.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Категорија:</span>
                  <Badge variant="secondary">{categoryLabel(report.category_id)}</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <History className="h-5 w-5" /> Историја на статус
                </CardTitle>
              </CardHeader>
              <CardContent>
                <StatusTimeline entries={historyEntries} />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <CommentsSection reportId={report.id} comments={report.comments} />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
