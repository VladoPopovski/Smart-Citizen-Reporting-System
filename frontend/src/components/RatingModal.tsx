import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Star, Loader2 } from "lucide-react";
import { createRating } from "@/services/reports";
import { useToast } from "@/hooks/use-toast";

interface Props {
  reportId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function RatingModal({ reportId, isOpen, onClose }: Props) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [stars, setStars] = useState(0);
  const [hoveredStars, setHoveredStars] = useState(0);
  const [comment, setComment] = useState("");

  const mutation = useMutation({
    mutationFn: () => createRating(reportId, { stars, comment: comment.trim() || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", reportId] });
      queryClient.invalidateQueries({ queryKey: ["rating", reportId] });
      toast({ title: "Успешно!", description: "Ви благодариме за вашата оцена." });
      onClose();
    },
    onError: (err: any) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно зачувување на оцената.",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (stars === 0) {
      toast({ title: "Внимание", description: "Ве молиме изберете оцена.", variant: "destructive" });
      return;
    }
    mutation.mutate();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Оцени ја пријавата</DialogTitle>
            <DialogDescription>
              Вашето мислење е важно за нас. Ве молиме одвојте момент за да го оцените искуството.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-6">
            <div className="flex flex-col items-center gap-3">
              <Label className="text-sm font-medium">Вашата оцена</Label>
              <div className="flex gap-1" role="group" aria-label="Оцена со ѕвезди">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className="transition-transform hover:scale-110 focus:outline-none"
                    onMouseEnter={() => setHoveredStars(star)}
                    onMouseLeave={() => setHoveredStars(0)}
                    onClick={() => setStars(star)}
                    aria-label={`${star} ѕвезди`}
                    aria-pressed={stars === star}
                  >
                    <Star
                      className={`h-8 w-8 ${
                        (hoveredStars || stars) >= star
                          ? "fill-yellow-400 text-yellow-400"
                          : "text-muted-foreground"
                      }`}
                      aria-hidden="true"
                    />
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="comment">Коментар (опционално)</Label>
              <Textarea
                id="comment"
                placeholder="Напишете ги вашите впечатоци..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="resize-none"
                rows={3}
                aria-label="Опционален коментар за оцената"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} disabled={mutation.isPending}>
              Откажи
            </Button>
            <Button type="submit" disabled={stars === 0 || mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Поднеси оцена
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
