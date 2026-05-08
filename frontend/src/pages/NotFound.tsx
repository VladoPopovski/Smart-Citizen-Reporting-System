import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FileQuestion, ChevronLeft } from "lucide-react";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="text-center space-y-6 max-w-md">
        <div className="flex justify-center">
          <div className="rounded-full bg-muted p-6">
            <FileQuestion className="h-16 w-16 text-muted-foreground" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">404</h1>
          <h2 className="text-2xl font-semibold">Страницата не е пронајдена</h2>
          <p className="text-muted-foreground text-lg">
            Се извинуваме, страницата што ја барате не постои или е преместена.
          </p>
        </div>

        <div className="pt-4">
          <Button 
            variant="default" 
            size="lg" 
            onClick={() => navigate("/")}
            className="gap-2"
          >
            <ChevronLeft className="h-4 w-4" /> Назад на почетна
          </Button>
        </div>
      </div>
    </div>
  );
}
