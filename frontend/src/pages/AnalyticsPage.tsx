import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyticsStats } from "@/data/mockData";
import { TrendingUp, FileText, CheckCircle, Clock, Users } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from "recharts";

const categoryData = [
  { name: "Инфраструктура", complaints: 380, resolved: 250 },
  { name: "Комунални", complaints: 320, resolved: 210 },
  { name: "Администрација", complaints: 180, resolved: 120 },
  { name: "Безбедност", complaints: 220, resolved: 140 },
];

const monthlyData = [
  { month: "Јан", complaints: 80, resolved: 55 },
  { month: "Фев", complaints: 95, resolved: 70 },
  { month: "Мар", complaints: 120, resolved: 88 },
  { month: "Апр", complaints: 140, resolved: 105 },
  { month: "Мај", complaints: 175, resolved: 130 },
  { month: "Јун", complaints: 200, resolved: 155 },
];

const pieData = [
  { name: "Решени", value: 65.4 },
  { name: "Нерешени", value: 34.6 },
];

const COLORS = ["hsl(142, 71%, 45%)", "hsl(220, 13%, 91%)"];

export default function AnalyticsPage() {
  const statCards = [
    { label: "ВКУПНО ПРИЈАВИ", value: analyticsStats.totalComplaints, icon: FileText, trend: "+12.5%", color: "text-primary" },
    { label: "РЕШЕНИ СЛУЧАИ", value: analyticsStats.resolvedCases, icon: CheckCircle, trend: "+8.2%", color: "text-success" },
    { label: "ПРОСЕЧНО ВРЕМЕ", value: analyticsStats.avgResolutionTime, icon: Clock, trend: "-1.1 ден", color: "text-warning" },
    { label: "АКТИВНИ ГРАЃАНИ", value: analyticsStats.activeCitizens.toLocaleString(), icon: Users, trend: "+5.4%", color: "text-info" },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Аналитички преглед</h1>
          <p className="text-muted-foreground text-sm">Следете ги перформансите и задоволството на граѓаните во реално време.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((s) => (
            <Card key={s.label}>
              <CardContent className="py-5 space-y-2">
                <div className="flex items-center justify-between">
                  <s.icon className={`h-5 w-5 ${s.color}`} />
                  <span className="text-xs font-medium text-success flex items-center gap-0.5">
                    <TrendingUp className="h-3 w-3" /> {s.trend}
                  </span>
                </div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground font-medium">{s.label}</p>
                <p className="text-2xl font-bold text-foreground">{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Пријави по категорија</CardTitle>
              <p className="text-xs text-muted-foreground">Дистрибуција по оддел (последни 30 дена)</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="complaints" name="Пријави" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="resolved" name="Решени" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Стапка на решавање</CardTitle>
              <p className="text-xs text-muted-foreground">Решени наспроти нерешени</p>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" strokeWidth={0}>
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <p className="text-3xl font-bold text-foreground -mt-2">65.4%</p>
              <p className="text-xs text-muted-foreground">Стапка на успешност</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Месечен тренд</CardTitle>
            <p className="text-xs text-muted-foreground">Споредба меѓу пристигнати пријави и решени случаи во 2024</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="complaints" name="Пријави" stroke="hsl(217, 91%, 60%)" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="resolved" name="Решени" stroke="hsl(142, 71%, 45%)" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
