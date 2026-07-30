import { createFileRoute } from "@tanstack/react-router";
import { ajouterCapacite, creerCompte, retirerCapacite } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { TitrePage } from "@/components/ui-siptrack";
import { LIBELLE_CAPACITE, TOUTES_CAPACITES } from "@/domaine/libelles";
import type { Capacite, Compte } from "@/api/types";
import { useState } from "react";
import { toast } from "sonner";
import { signalerErreur } from "@/domaine/erreurs";
import { User } from "lucide-react";

export const Route = createFileRoute("/equipe")({
  head: () => ({
    meta: [
      { title: "Équipe & accès — SipTrack" },
      { name: "description", content: "Comptes et capacités du bar." },
    ],
  }),
  component: PageEquipe,
});

function PageEquipe() {
  const { barId } = useSession();
  const [userId, setUserId] = useState("");
  const [initiales, setInitiales] = useState<Set<Capacite>>(new Set(["enregistrer_vente", "encaisser"]));
  const [dernier, setDernier] = useState<Compte | null>(null);

  const mCreer = useEcriture(
    (_: void, cle) => creerCompte(barId as string, userId.trim(), Array.from(initiales), cle),
    {
      onSuccess: (c) => {
        toast.success("Compte créé.");
        setDernier(c);
        setUserId("");
      },
      onError: signalerErreur,
    },
  );

  return (
    <div>
      <TitrePage titre="Équipe & accès" sous="Attribution des capacités par personne." />

      <div className="rounded-xl border border-border bg-card p-4">
        <h2 className="mb-2 font-semibold">Créer un compte</h2>
        <p className="mb-3 text-xs text-muted-foreground">
          Renseignez l'identifiant utilisateur (fourni par la plateforme) et les capacités initiales.
        </p>
        <div className="space-y-2">
          <Label>Identifiant utilisateur</Label>
          <Input
            icone={User}
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="user_id"
          />
          <div className="mt-2 grid grid-cols-1 gap-2">
            {TOUTES_CAPACITES.map((c) => (
              <label key={c} className="flex items-center justify-between rounded-md border border-border p-2 text-sm">
                <span>{LIBELLE_CAPACITE[c]}</span>
                <Switch
                  checked={initiales.has(c)}
                  onCheckedChange={(v) => {
                    const s = new Set(initiales);
                    if (v) s.add(c);
                    else s.delete(c);
                    setInitiales(s);
                  }}
                />
              </label>
            ))}
          </div>
          <Button className="mt-3 h-12 w-full" disabled={mCreer.isPending || !userId.trim()} onClick={() => mCreer.mutate()}>
            {mCreer.isPending ? "Création…" : "Créer le compte"}
          </Button>
        </div>
      </div>

      {dernier ? <BlocCompte compte={dernier} onChange={setDernier} /> : null}
    </div>
  );
}

function BlocCompte({ compte, onChange }: { compte: Compte; onChange: (c: Compte) => void }) {
  const mAjout = useEcriture((c: Capacite, cle) => ajouterCapacite(compte.id, c, cle), {
    onSuccess: (c) => { onChange(c); toast.success("Capacité accordée."); },
    onError: signalerErreur,
  });
  const mRetrait = useEcriture((c: Capacite, cle) => retirerCapacite(compte.id, c, cle), {
    onSuccess: (c) => { onChange(c); toast.success("Capacité retirée."); },
    onError: signalerErreur,
  });
  return (
    <div className="mt-4 rounded-xl border border-border bg-card p-4">
      <h2 className="mb-2 font-semibold">Compte {compte.id.slice(0, 8)}</h2>
      <p className="mb-3 text-xs text-muted-foreground">Utilisateur : {compte.user_id}</p>
      <div className="space-y-2">
        {TOUTES_CAPACITES.map((c) => {
          const on = compte.capacites.includes(c);
          const busy = mAjout.isPending || mRetrait.isPending;
          return (
            <label key={c} className="flex items-center justify-between rounded-md border border-border p-2 text-sm">
              <span>{LIBELLE_CAPACITE[c]}</span>
              <Switch
                checked={on}
                disabled={busy}
                onCheckedChange={(v) => (v ? mAjout.mutate(c) : mRetrait.mutate(c))}
              />
            </label>
          );
        })}
      </div>
    </div>
  );
}
