import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Beer } from "lucide-react";
import { authJeton } from "@/api/endpoints";
import { definirJeton, useSession } from "@/etat/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/connexion")({
  head: () => ({
    meta: [
      { title: "Connexion — SipTrack" },
      { name: "description", content: "Accès au registre du bar." },
      { property: "og:title", content: "Connexion — SipTrack" },
    ],
  }),
  component: PageConnexion,
});

function PageConnexion() {
  const nav = useNavigate();
  const { jeton } = useSession();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [encours, setEncours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  if (jeton) {
    // Déjà connectée → laisse la coque router.
    setTimeout(() => nav({ to: "/bars" }), 0);
  }

  async function soumettre(e: React.FormEvent) {
    e.preventDefault();
    setErreur(null);
    setEncours(true);
    try {
      const rep = await authJeton(u, p);
      if (rep.status === 429) {
        setErreur("Trop de tentatives. Réessayez dans une minute.");
      } else if (!rep.ok) {
        const corps = await rep.json().catch(() => ({}));
        const msg =
          corps?.non_field_errors?.[0] ??
          corps?.detail ??
          "Identifiants refusés. Vérifiez votre saisie.";
        setErreur(msg);
      } else {
        const { token } = await rep.json();
        definirJeton(token);
        toast.success("Bienvenue.");
        nav({ to: "/bars" });
      }
    } catch {
      setErreur("Le service est injoignable. Vérifiez votre connexion.");
    } finally {
      setEncours(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={soumettre} className="w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="mb-6 flex items-center gap-2">
          <Beer className="h-6 w-6 text-primary" />
          <div>
            <div className="text-lg font-semibold">SipTrack</div>
            <div className="text-xs text-muted-foreground">Le registre du bar.</div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="u">Identifiant</Label>
            <Input id="u" autoComplete="username" value={u} onChange={(e) => setU(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p">Mot de passe</Label>
            <Input
              id="p"
              type="password"
              autoComplete="current-password"
              value={p}
              onChange={(e) => setP(e.target.value)}
              required
            />
          </div>
          {erreur ? (
            <div className="rounded-md border border-manquant/30 bg-manquant/10 p-3 text-sm text-manquant">
              {erreur}
            </div>
          ) : null}
          <Button type="submit" disabled={encours} className="h-12 w-full text-base">
            {encours ? "Connexion…" : "Se connecter"}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            Les comptes sont créés par la gérante.
          </p>
        </div>
      </form>
    </div>
  );
}
