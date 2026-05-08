import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { AlertCircle, ChevronLeft, RefreshCcw } from "lucide-react";

export default function ServerError() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="text-center space-y-6 max-w-md">
        <div className="flex justify-center">
          <div className="rounded-full bg-destructive/10 p-6">
            <AlertCircle className="h-16 w-16 text-destructive" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">500</h1>
          <h2 className="text-2xl font-semibold">Серверска грешка</h2>
          <p className="text-muted-foreground text-lg">
            Се појави неочекуван проблем на нашиот сервер. Ве молиме обидете се повторно подоцна.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
          <Button 
            variant="default" 
            size="lg" 
            onClick={() => window.location.reload()}
            className="gap-2"
          >
            <RefreshCcw className="h-4 w-4" /> Обиди се повторно
          </Button>
          <Button 
            variant="outline" 
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
