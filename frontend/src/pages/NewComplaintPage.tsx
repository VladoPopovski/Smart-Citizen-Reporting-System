import { useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { categories } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function NewComplaintPage() {
  const { toast } = useToast();
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!category || description.length < 20) {
      toast({
        title: "Грешка при валидација",
        description: "Изберете категорија и внесете најмалку 20 карактери за описот.",
        variant: "destructive",
      });
      return;
    }

    const data = { category, description, date: new Date().toISOString() };
    console.log("Нова пријава поднесена:", data);

    toast({ title: "Успешно!", description: "Вашата пријава е успешно поднесена." });
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <AppLayout>
        <div className="max-w-lg mx-auto text-center py-20 space-y-4">
          <CheckCircle className="h-16 w-16 text-success mx-auto" />
          <h2 className="text-2xl font-bold text-foreground">Пријавата е поднесена!</h2>
          <p className="text-muted-foreground">Вашата пријава е примена. Ќе ја прегледаме и ќе ја доделиме на соодветниот оддел.</p>
          <Button onClick={() => { setSubmitted(false); setCategory(""); setDescription(""); }}>
            Поднеси уште една
          </Button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Нова пријава</h1>
          <p className="text-muted-foreground text-sm">Пополнете ги деталите подолу за да пријавите проблем во вашата заедница.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Детали за проблемот</CardTitle>
              <p className="text-sm text-muted-foreground">Обидете се да бидете што попрецизни при описот на ситуацијата.</p>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="category">Категорија на пријава</Label>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger id="category"><SelectValue placeholder="Изберете категорија" /></SelectTrigger>
                  <SelectContent>
                    {categories.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Детален опис</Label>
                <Textarea
                  id="description"
                  placeholder="Опишете го проблемот овде... На пример: Има голема дупка на средината на патот која ги оштетува возилата."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={5}
                />
                <p className="text-xs text-muted-foreground italic">Минимум 20 карактери за подобра обработка од страна на властите.</p>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => { setCategory(""); setDescription(""); }}>
                  Откажи
                </Button>
                <Button type="submit">
                  Поднеси пријава
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      </div>
    </AppLayout>
  );
}