import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Bell, Mail, Shield, User as UserIcon, Loader2, Key } from "lucide-react";
import { fetchUserProfile, updateUserSettings } from "@/services/users";
import { useRole } from "@/context/RoleContext";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { supabase } from "@/lib/supabase";

export default function SettingsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { userName, role } = useRole();
  const [newPassword, setNewPassword] = useState("");
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const { data: user, isLoading } = useQuery({
    queryKey: ["user", "me"],
    queryFn: fetchUserProfile,
  });

  const mutation = useMutation({
    mutationFn: (emailNotifications: boolean) => updateUserSettings({ email_notifications: emailNotifications }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "me"] });
      toast({ title: "Поставките се зачувани", description: "Вашите измени беа успешно зачувани." });
    },
    onError: (err: any) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно зачувување на поставките.",
        variant: "destructive",
      });
    },
  });

  const handleChangePassword = async () => {
    if (newPassword.length < 6) {
      toast({ 
        title: "Внимание", 
        description: "Лозинката мора да има најмалку 6 карактери.", 
        variant: "destructive" 
      });
      return;
    }

    setIsChangingPassword(true);
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw error;
      toast({ title: "Успешно", description: "Вашата лозинка е променета." });
      setNewPassword("");
      setIsPasswordModalOpen(false);
    } catch (err: any) {
      toast({ 
        title: "Грешка", 
        description: err.message ?? "Грешка при промена на лозинка.", 
        variant: "destructive" 
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <Skeleton className="h-10 w-48" />
        <Card aria-busy="true">
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Поставки</h1>
        <p className="text-muted-foreground text-sm">Управувајте со вашата сметка и известувања.</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <UserIcon className="h-5 w-5 text-primary" aria-hidden="true" />
            <CardTitle className="text-lg">Профил</CardTitle>
          </div>
          <CardDescription>Основни информации за вашата сметка.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-1">
            <Label className="text-xs text-muted-foreground">Е-пошта</Label>
            <p className="font-medium" aria-label={`Е-пошта: ${user?.email}`}>{user?.email}</p>
          </div>
          <div className="grid gap-1">
            <Label className="text-xs text-muted-foreground">Име / Прекар</Label>
            <p className="font-medium" aria-label={`Име: ${userName}`}>{userName}</p>
          </div>
          <div className="grid gap-1">
            <Label className="text-xs text-muted-foreground">Улога</Label>
            <p className="font-medium capitalize" aria-label={`Улога во системот`}>
              {role === "citizen" ? "Граѓанин" : role === "officer" ? "Службеник" : "Администратор"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" aria-hidden="true" />
            <CardTitle className="text-lg">Известувања</CardTitle>
          </div>
          <CardDescription>Изберете како сакате да бидете информирани за вашите пријави.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between space-x-2">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <Label htmlFor="email-notifications">Е-маил известувања</Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Добивајте известувања кога статусот на вашата пријава ќе се промени.
              </p>
            </div>
            <Switch
              id="email-notifications"
              checked={user?.settings?.email_notifications ?? false}
              onCheckedChange={(checked) => mutation.mutate(checked)}
              disabled={mutation.isPending}
              aria-label="Вклучи или исклучи е-маил известувања"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" aria-hidden="true" />
            <CardTitle className="text-lg">Приватност и безбедност</CardTitle>
          </div>
          <CardDescription>Управување со лозинката и сесиите.</CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={isPasswordModalOpen} onOpenChange={setIsPasswordModalOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2" aria-label="Отвори дијалог за промена на лозинка">
                <Key className="h-4 w-4" aria-hidden="true" /> Промени лозинка
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Промена на лозинка</DialogTitle>
                <DialogDescription>
                  Внесете ја вашата нова лозинка. Потребно е да има најмалку 6 карактери.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="new-password">Нова лозинка</Label>
                  <Input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="******"
                    aria-required="true"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button 
                  type="button" 
                  variant="ghost" 
                  onClick={() => setIsPasswordModalOpen(false)}
                  disabled={isChangingPassword}
                >
                  Откажи
                </Button>
                <Button 
                  type="button" 
                  onClick={handleChangePassword}
                  disabled={!newPassword || isChangingPassword}
                >
                  {isChangingPassword && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Зачувај лозинка
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
