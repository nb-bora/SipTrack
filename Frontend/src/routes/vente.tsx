import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { enregistrerVente, listerProduits } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { lireServiceCourant } from "@/etat/local";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Montant, TitrePage } from "@/components/ui-siptrack";
import { LIBELLE_FORME } from "@/domaine/libelles";
import type { FormePaiement, Produit } from "@/api/types";
import { signalerErreur } from "@/domaine/erreurs";
import { toast } from "sonner";
import { Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

// Au comptoir, pas de client désigné : le crédit n'y a pas sa place.
const FORMES_COMPTOIR: FormePaiement[] = ["especes", "mobile_money"];

export const Route = createFileRoute("/vente")({
  head: () => ({
    meta: [
      { title: "Vente rapide — SipTrack" },
      { name: "description", content: "Vente au comptoir." },
    ],
  }),
  component: PageVente,
});

function PageVente() {
  const { barId } = useSession();
  const nav = useNavigate();
  const qc = useQueryClient();
  const serviceId = barId ? lireServiceCourant(barId) : null;

  const [selection, setSelection] = useState<Produit | null>(null);
  const [q, setQ] = useState(1);
  const [forme, setForme] = useState<FormePaiement>("especes");

  const rq = useQuery({
    queryKey: ["produits", barId],
    queryFn: () => listerProduits(barId as string),
    enabled: !!barId,
  });

  const produits = useMemo(() => (rq.data ?? []).filter((p) => p.en_vente), [rq.data]);

  const m = useEcriture(
    (_: void, cle) =>
      enregistrerVente(
        serviceId as string,
        {
          produit_id: selection!.id,
          quantite: q,
          forme_paiement: forme,
        },
        cle,
      ),
    {
      onSuccess: (v) => {
        toast.success(`Vente enregistrée : ${v.quantite} × ${selection?.nom}.`);
        setSelection(null);
        setQ(1);
        setForme("especes");
        qc.invalidateQueries({ queryKey: ["service", serviceId] });
      },
      onError: signalerErreur,
    },
  );

  if (!serviceId) {
    return (
      <div>
        <TitrePage titre="Vente rapide" />
        <p className="text-sm text-muted-foreground">
          Aucun service en cours.{" "}
          <button onClick={() => nav({ to: "/accueil" })} className="text-primary underline">
            Ouvrir un service
          </button>
          .
        </p>
      </div>
    );
  }

  return (
    <div>
      <TitrePage titre="Vente rapide" sous="Sélectionnez un produit du catalogue." />
      {rq.isLoading ? (
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : produits.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
          Aucun produit en vente. Ajoutez-en dans « Catalogue ».
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          {produits.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelection(p)}
              className={cn(
                "flex min-h-[96px] flex-col items-start justify-between rounded-lg border-2 bg-card p-3 text-left transition",
                selection?.id === p.id ? "border-primary" : "border-border hover:border-primary/60",
              )}
            >
              <span className="text-sm font-semibold leading-tight">{p.nom}</span>
              <Montant valeur={p.prix} taille="md" />
            </button>
          ))}
        </div>
      )}

      {selection ? (
        <div className="mt-4 rounded-xl border border-border bg-card p-4">
          <div className="flex items-baseline justify-between">
            <span className="font-semibold">{selection.nom}</span>
            <Montant valeur={selection.prix * q} taille="lg" />
          </div>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Quantité</span>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-12 w-12"
                onClick={() => setQ((x) => Math.max(1, x - 1))}
              >
                <Minus className="h-5 w-5" />
              </Button>
              <span className="montant w-10 text-center text-xl font-bold">{q}</span>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-12 w-12"
                onClick={() => setQ((x) => x + 1)}
              >
                <Plus className="h-5 w-5" />
              </Button>
            </div>
          </div>
          <div className="mt-3">
            <div className="mb-1 text-sm text-muted-foreground">Forme de paiement</div>
            <div className="grid grid-cols-2 gap-2">
              {FORMES_COMPTOIR.map((f) => (
                <button
                  key={f}
                  onClick={() => setForme(f)}
                  className={cn(
                    "min-h-[48px] rounded-md border-2 px-2 text-sm",
                    forme === f ? "border-primary text-primary" : "border-border text-foreground",
                  )}
                >
                  {LIBELLE_FORME[f]}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Le crédit n'est pas proposé ici : une vente au comptoir ne désigne aucun débiteur,
              donc aucune créance ne pourrait être ouverte. Pour laisser une ardoise, ouvrez une
              table et encaissez-la en crédit au nom d'un client.
            </p>
          </div>
          <p className="mt-3 text-[11px] text-muted-foreground">
            Le prix vient du catalogue. Le montant définitif est celui rendu par le serveur.
          </p>
          <Button
            className="mt-3 h-12 w-full text-base"
            disabled={m.isPending}
            onClick={() => m.mutate()}
          >
            {m.isPending ? "Enregistrement…" : `Enregistrer la vente`}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
