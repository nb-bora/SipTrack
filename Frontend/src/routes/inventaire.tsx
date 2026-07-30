import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { corrigerInventaire, inscrireStock, ajusterStock, listerStock } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TitrePage } from "@/components/ui-siptrack";
import type { ProduitStock } from "@/api/types";
import { useState } from "react";
import { toast } from "sonner";
import { signalerErreur } from "@/domaine/erreurs";
import { FileText, Hash, Package } from "lucide-react";

export const Route = createFileRoute("/inventaire")({
  head: () => ({
    meta: [
      { title: "Inventaire — SipTrack" },
      { name: "description", content: "Stocks et corrections d'inventaire." },
    ],
  }),
  component: PageInv,
});

function PageInv() {
  const { barId } = useSession();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["stock", barId],
    queryFn: () => listerStock(barId as string),
    enabled: !!barId,
  });
  const [nom, setNom] = useState("");
  const [qte, setQte] = useState("");
  const mCreer = useEcriture(
    (_: void, cle) => inscrireStock(barId as string, nom.trim(), parseInt(qte, 10) || 0, cle),
    {
      onSuccess: () => {
        toast.success("Produit d'inventaire créé.");
        setNom(""); setQte("");
        qc.invalidateQueries({ queryKey: ["stock", barId] });
      },
      onError: signalerErreur,
    },
  );

  return (
    <div>
      <TitrePage titre="Inventaire" sous="Distinct du catalogue : ce sont deux objets différents." />
      <form
        onSubmit={(e) => { e.preventDefault(); if (nom.trim() && qte) mCreer.mutate(); }}
        className="mb-4 grid grid-cols-[1fr_120px_auto] gap-2"
      >
        <Input
          icone={Package}
          placeholder="Nom"
          value={nom}
          onChange={(e) => setNom(e.target.value)}
        />
        <Input
          icone={Hash}
          inputMode="numeric"
          pattern="[0-9]*"
          placeholder="Qté initiale"
          value={qte}
          onChange={(e) => setQte(e.target.value.replace(/\D/g, ""))}
        />
        <Button type="submit" disabled={mCreer.isPending || !nom.trim() || !qte}>
          {mCreer.isPending ? "…" : "Ajouter"}
        </Button>
      </form>
      {q.isLoading ? (
        <div className="h-24 animate-pulse rounded-xl bg-muted" />
      ) : (
        <ul className="space-y-2">
          {q.data?.map((p) => <LigneStock key={p.id} p={p} />)}
        </ul>
      )}
    </div>
  );
}

function LigneStock({ p }: { p: ProduitStock }) {
  const qc = useQueryClient();
  const [ajout, setAjout] = useState("");
  const [nouvQte, setNouvQte] = useState("");
  const [raison, setRaison] = useState("");
  const [mode, setMode] = useState<"aucun" | "ajout" | "correction">("aucun");

  const mAjout = useEcriture((_: void, cle) => ajusterStock(p.id, parseInt(ajout, 10) || 0, cle), {
    onSuccess: () => {
      toast.success("Stock ajouté.");
      qc.invalidateQueries({ queryKey: ["stock", p.bar_id] });
      setAjout(""); setMode("aucun");
    },
    onError: signalerErreur,
  });
  const mCorr = useEcriture(
    (_: void, cle) => corrigerInventaire(p.id, parseInt(nouvQte, 10) || 0, raison.trim(), cle),
    {
      onSuccess: () => {
        toast.success("Inventaire corrigé.");
        qc.invalidateQueries({ queryKey: ["stock", p.bar_id] });
        setNouvQte(""); setRaison(""); setMode("aucun");
      },
      onError: signalerErreur,
    },
  );

  return (
    <li className="rounded-lg border border-border bg-card p-3">
      <div className="flex items-baseline justify-between">
        <div className="font-semibold">{p.nom}</div>
        <div className="montant text-xl font-bold">{p.quantite}</div>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={() => setMode(mode === "ajout" ? "aucun" : "ajout")}>
          Ajouter du stock
        </Button>
        <Button size="sm" variant="outline" onClick={() => setMode(mode === "correction" ? "aucun" : "correction")}>
          Corriger l'inventaire
        </Button>
      </div>

      {mode === "ajout" ? (
        <div className="mt-3 space-y-2">
          <Label>Quantité à ajouter</Label>
          <Input
            icone={Hash}
            inputMode="numeric"
            pattern="[0-9]*"
            value={ajout}
            onChange={(e) => setAjout(e.target.value.replace(/\D/g, ""))}
          />
          <Button className="w-full" disabled={mAjout.isPending || !ajout} onClick={() => mAjout.mutate()}>
            {mAjout.isPending ? "…" : "Ajouter"}
          </Button>
        </div>
      ) : null}

      {mode === "correction" ? (
        <div className="mt-3 space-y-2">
          <Label>Quantité constatée après comptage</Label>
          <Input
            icone={Hash}
            inputMode="numeric"
            pattern="[0-9]*"
            value={nouvQte}
            onChange={(e) => setNouvQte(e.target.value.replace(/\D/g, ""))}
          />
          <Label>Raison (obligatoire — c'est ce qui rend l'écart opposable)</Label>
          <Input icone={FileText} value={raison} onChange={(e) => setRaison(e.target.value)} />
          <Button
            className="w-full"
            disabled={mCorr.isPending || !nouvQte || !raison.trim()}
            onClick={() => mCorr.mutate()}
          >
            {mCorr.isPending ? "…" : "Enregistrer la correction"}
          </Button>
        </div>
      ) : null}
    </li>
  );
}
