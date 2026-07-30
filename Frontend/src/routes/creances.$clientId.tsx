import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getEncoursClient, rembourserCredit } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LigneKV, Montant, TitrePage } from "@/components/ui-siptrack";
import { useState } from "react";
import { toast } from "sonner";
import { signalerErreur } from "@/domaine/erreurs";
import { Coins } from "lucide-react";

export const Route = createFileRoute("/creances/$clientId")({
  head: () => ({
    meta: [
      { title: "Détail créance — SipTrack" },
      { name: "description", content: "Créances d'un client et remboursements." },
    ],
  }),
  component: PageClient,
});

function PageClient() {
  const { clientId } = Route.useParams();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["encours-client", clientId],
    queryFn: () => getEncoursClient(clientId),
  });
  const [choix, setChoix] = useState<string | null>(null);
  const [montant, setMontant] = useState("");
  const [confirme, setConfirme] = useState(false);

  const m = useEcriture(
    (_: void, cle) => rembourserCredit(choix as string, parseInt(montant || "0", 10) || 0, cle),
    {
      onSuccess: () => {
        toast.success("Remboursement enregistré.");
        qc.invalidateQueries({ queryKey: ["encours-client", clientId] });
        qc.invalidateQueries({ queryKey: ["encours-bar"] });
        setChoix(null);
        setMontant("");
        setConfirme(false);
      },
      onError: (e) => {
        signalerErreur(e);
        setConfirme(false);
      },
    },
  );

  if (q.isLoading) return <div className="h-40 animate-pulse rounded-xl bg-muted" />;
  if (q.isError || !q.data) return <p className="text-sm text-manquant">Client introuvable.</p>;

  const e = q.data;
  const creanceChoisie = e.creances.find((x) => x.credit_id === choix);
  const n = parseInt(montant || "0", 10) || 0;

  return (
    <div>
      <TitrePage titre={e.client_nom} />
      <div className="rounded-xl border border-border bg-card p-4">
        <LigneKV k="Total dû" v={<Montant valeur={e.total_du} taille="md" />} />
        <LigneKV k="Total remboursé" v={<Montant valeur={e.total_rembourse} taille="md" ton="muted" />} />
        <div className="mt-2 flex items-baseline justify-between border-t border-border pt-3">
          <span className="text-sm font-semibold uppercase text-muted-foreground">Reste</span>
          <Montant valeur={e.reste} taille="xl" ton="manquant" />
        </div>
      </div>

      <h2 className="mt-6 mb-2 text-sm uppercase tracking-wide text-muted-foreground">Créances</h2>
      <ul className="space-y-2">
        {e.creances.map((c) => (
          <li
            key={c.credit_id}
            className={
              "rounded-lg border bg-card p-3 " +
              (choix === c.credit_id ? "border-primary" : "border-border")
            }
          >
            <button className="w-full text-left" onClick={() => { setChoix(c.credit_id); setMontant(String(c.reste)); }}>
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-muted-foreground">Créance {c.credit_id.slice(0, 8)}</span>
                <Montant valeur={c.reste} ton={c.reste === 0 ? "solde" : "manquant"} />
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                Origine addition {c.addition_id.slice(0, 8)} · statut {c.statut}
              </div>
            </button>
          </li>
        ))}
      </ul>

      {creanceChoisie ? (
        <form
          onSubmit={(ev) => {
            ev.preventDefault();
            if (!confirme) return setConfirme(true);
            if (n > 0) m.mutate();
          }}
          className="mt-4 rounded-xl border border-border bg-card p-4 space-y-3"
        >
          <div>
            <Label>Montant du remboursement</Label>
            <Input
              icone={Coins}
              inputMode="numeric"
              pattern="[0-9]*"
              value={montant}
              onChange={(e) => {
                setMontant(e.target.value.replace(/\D/g, ""));
                setConfirme(false);
              }}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Reste de cette créance : <Montant valeur={creanceChoisie.reste} taille="sm" />
            </p>
          </div>
          {confirme ? (
            <div className="rounded-md bg-muted p-3 text-sm">
              Confirmez le remboursement de <Montant valeur={n} taille="md" /> ?
            </div>
          ) : null}
          <Button className="h-12 w-full" disabled={m.isPending || n <= 0}>
            {m.isPending ? "Enregistrement…" : confirme ? "Confirmer" : "Encaisser le remboursement"}
          </Button>
        </form>
      ) : null}
    </div>
  );
}
