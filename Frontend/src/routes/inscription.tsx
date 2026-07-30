import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Beer, Lock, Mail, Store, User } from "lucide-react";
import { inscrire } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/inscription")({
  head: () => ({
    meta: [
      { title: "Inscription — SipTrack" },
      { name: "description", content: "Créer un compte et votre premier bar." },
      { property: "og:title", content: "Inscription — SipTrack" },
    ],
  }),
  component: PageInscription,
});

function PageInscription() {
  const nav = useNavigate();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [pv, setPv] = useState("");
  const [courriel, setCourriel] = useState("");
  const [nb, setNb] = useState("");
  const [encours, setEncours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  async function soumettre(ev: React.FormEvent) {
    ev.preventDefault();
    setErreur(null);

    if (p !== pv) {
      setErreur("Les mots de passe ne correspondent pas.");
      return;
    }

    if (p.length < 8) {
      setErreur("Le mot de passe doit faire au moins 8 caractères.");
      return;
    }

    setEncours(true);
    try {
      const rep = await inscrire(u, p, nb, courriel || undefined);

      if (!rep.ok) {
        const corps = await rep.json().catch(() => ({}));
        const msg =
          corps?.detail ??
          corps?.non_field_errors?.[0] ??
          corps?.username?.[0] ??
          corps?.nom_bar?.[0] ??
          "Inscription échouée. Vérifiez vos données.";
        setErreur(msg);
      } else {
        const { bar_nom, message } = await rep.json();
        toast.success(`${message} Bienvenue dans ${bar_nom}.`);
        // Rediriger vers login après succès
        setTimeout(() => nav({ to: "/connexion" }), 1500);
      }
    } catch {
      setErreur("Le service est injoignable. Vérifiez votre connexion.");
    } finally {
      setEncours(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={soumettre}
        className="w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-lg"
      >
        <div className="mb-6 flex items-center gap-2">
          <Beer className="h-6 w-6 text-primary" />
          <div>
            <div className="text-lg font-semibold">SipTrack</div>
            <div className="text-xs text-muted-foreground">Créer un compte.</div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="u">Identifiant</Label>
            <Input
              id="u"
              icone={User}
              autoComplete="username"
              value={u}
              onChange={(e) => setU(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="nb">Nom du bar</Label>
            <Input
              id="nb"
              icone={Store}
              value={nb}
              onChange={(e) => setNb(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="courriel">Email (optionnel)</Label>
            <Input
              id="courriel"
              type="email"
              icone={Mail}
              autoComplete="email"
              value={courriel}
              onChange={(ev) => setCourriel(ev.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="p">Mot de passe</Label>
            <Input
              id="p"
              type="password"
              icone={Lock}
              autoComplete="new-password"
              value={p}
              onChange={(e) => setP(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">Minimum 8 caractères.</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pv">Confirmer le mot de passe</Label>
            <Input
              id="pv"
              type="password"
              icone={Lock}
              autoComplete="new-password"
              value={pv}
              onChange={(e) => setPv(e.target.value)}
              required
            />
          </div>

          {erreur ? (
            <div className="rounded-md border border-manquant/30 bg-manquant/10 p-3 text-sm text-manquant">
              {erreur}
            </div>
          ) : null}

          <Button type="submit" disabled={encours} className="h-12 w-full text-base">
            {encours ? "Inscription…" : "S'inscrire"}
          </Button>

          <p className="text-center text-xs text-muted-foreground">
            Vous avez déjà un compte ?{" "}
            <button
              type="button"
              onClick={() => nav({ to: "/connexion" })}
              className="font-medium text-primary hover:underline"
            >
              Se connecter
            </button>
          </p>
        </div>
      </form>
    </div>
  );
}
