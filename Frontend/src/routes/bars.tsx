import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { creerBar, listerBars } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { definirBar, useSession } from "@/etat/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { signalerErreur } from "@/domaine/erreurs";
import { TitrePage } from "@/components/ui-siptrack";
import { toast } from "sonner";
import { Store } from "lucide-react";

export const Route = createFileRoute("/bars")({
  head: () => ({
    meta: [
      { title: "Choix du bar — SipTrack" },
      { name: "description", content: "Choisir le bar sur lequel travailler." },
    ],
  }),
  component: PageBars,
});

function PageBars() {
  const nav = useNavigate();
  const { jeton } = useSession();
  const qc = useQueryClient();
  const [nom, setNom] = useState("");

  useEffect(() => {
    if (!jeton) nav({ to: "/connexion" });
  }, [jeton, nav]);

  const q = useQuery({
    queryKey: ["bars"],
    queryFn: listerBars,
    enabled: !!jeton,
  });

  useEffect(() => {
    if (q.data && q.data.length === 1) {
      definirBar(q.data[0].id);
      nav({ to: "/accueil" });
    }
  }, [q.data, nav]);

  const m = useEcriture((nom: string, cle) => creerBar(nom, cle), {
    onSuccess: (bar) => {
      toast.success("Bar créé.");
      qc.invalidateQueries({ queryKey: ["bars"] });
      definirBar(bar.id);
      nav({ to: "/accueil" });
    },
    onError: signalerErreur,
  });

  return (
    <div className="mx-auto max-w-md px-4 py-8">
      {/*
        La liste mêle désormais les bars que l'on possède et ceux où l'on tient
        simplement un compte : le titre ne peut plus présumer la possession.
        Distinguer les deux à l'écran suppose de connaître son propre user_id,
        que l'API n'expose pas encore — voir GET /api/moi/ (#67).
      */}
      <TitrePage titre="Où travaillez-vous ?" sous="Choisissez le bar sur lequel travailler." />
      {q.isLoading ? (
        <div className="space-y-2">
          <div className="h-16 animate-pulse rounded-lg bg-muted" />
          <div className="h-16 animate-pulse rounded-lg bg-muted" />
        </div>
      ) : q.isError ? (
        <p className="text-sm text-manquant">Impossible de charger vos bars.</p>
      ) : (
        <ul className="space-y-2">
          {q.data?.map((b) => (
            <li key={b.id}>
              <button
                onClick={() => {
                  definirBar(b.id);
                  nav({ to: "/accueil" });
                }}
                className="flex w-full items-center justify-between rounded-lg border border-border bg-card px-4 py-4 text-left hover:border-primary"
              >
                {/*
                  L'identifiant du propriétaire n'est plus affiché : c'est une
                  clé technique, illisible pour une gérante, et depuis que la
                  liste inclut les bars d'autrui elle désignerait une tierce
                  personne sans rien apprendre à qui la lit.
                */}
                <div className="font-semibold">{b.nom}</div>
                <span className="text-primary">→</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (nom.trim()) m.mutate(nom.trim());
        }}
        className="mt-8 rounded-lg border border-border bg-card p-4"
      >
        <h2 className="mb-2 font-semibold">Créer un bar</h2>
        <div className="flex gap-2">
          <Input
            icone={Store}
            placeholder="Nom du bar"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
          />
          <Button type="submit" disabled={m.isPending || !nom.trim()}>
            {m.isPending ? "Création…" : "Créer"}
          </Button>
        </div>
      </form>
    </div>
  );
}
