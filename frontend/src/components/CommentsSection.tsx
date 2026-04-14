import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { formatDate } from "@/lib/reportHelpers";

export interface Comment {
  id: number;
  user_id: string;
  content: string;
  created_at: string;
}

interface Props {
  initial: Comment[];
}

export function CommentsSection({ initial }: Props) {
  const [comments, setComments] = useState<Comment[]>(initial);
  const [text, setText] = useState("");

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setComments((prev) => [
      ...prev,
      {
        id: Date.now(),
        user_id: "current-user",
        content: trimmed,
        created_at: new Date().toISOString(),
      },
    ]);
    setText("");
  };

  return (
    <div className="space-y-4">
      {comments.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">Сè уште нема коментари.</p>
      ) : (
        <div className="space-y-3">
          {comments.map((c) => (
            <div key={c.id} className="rounded-md border bg-muted/30 p-3 space-y-1">
              <p className="text-sm text-foreground">{c.content}</p>
              <p className="text-xs text-muted-foreground">{formatDate(c.created_at)}</p>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        <Textarea
          placeholder="Напишете коментар…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
        />
        <Button size="sm" onClick={handleSubmit} disabled={!text.trim()}>
          Додади коментар
        </Button>
      </div>
    </div>
  );
}
