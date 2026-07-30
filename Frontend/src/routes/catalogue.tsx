import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { creerProduit, listerProduits, retirerProduit, tariferProduit } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Montant, TitrePage } from "@/components/ui-siptrack";
import { signalerErreur } from "@/domaine/erreurs";
import { useState } from "react";
import { toast } from "sonner";
import type { Produit } from "@/api/types";
import { cn } from "@/lib/utils";
import { Beer, Coins } from "lucide-react";

export const Route = createFileRoute("/catalogue")({
  head: () => ({
    meta: [
      { title: "Catalogue & tarifs — SipTrack" },
      { name: "description", content: "Gestion du catalogue et des tarifs." },
    ],
  }),
  component: PageCatalogue,
});

function PageCatalogue() {
  const { barId } = useSession();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["produits", barId],
    queryFn: () => listerProduits(barId as string),
    enabled: !!barId,
  });
  const [nom, setNom] = useState("");
  const [prix, setPrix] = useState("");
  const mCreer = useEcriture(
    (_: void, cle) => creerProduit(barId as string, nom.trim(), parseInt(prix, 10) || 0, cle),
    {
      onSuccess: () => {
        toast.success("Produit créé.");
        setNom("");
        setPrix("");
        qc.invalidateQueries({ queryKey: ["produits", barId] });
      },
      onError: signalerErreur,
    },
  );

  return (
    <div>
      <TitrePage
        titre="Catalogue & tarifs"
        sous="Les ventes déjà saisies gardent leur prix. Chaque changement est consigné."
      />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (nom.trim() && prix) mCreer.mutate();
        }}
        className="mb-4 grid grid-cols-[1fr_120px_auto] gap-2"
      >
        <Input
          icone={Beer}
          placeholder="Nom du produit"
          value={nom}
          onChange={(e) => setNom(e.target.value)}
        />
        <Input
          icone={Coins}
          inputMode="numeric"
          pattern="[0-9]*"
          placeholder="Prix"
          value={prix}
          onChange={(e) => setPrix(e.target.value.replace(/\D/g, ""))}
        />
        <Button type="submit" disabled={mCreer.isPending || !nom.trim() || !prix}>
          {mCreer.isPending ? "…" : "Ajouter"}
        </Button>
      </form>

      {q.isLoading ? (
        <div className="h-24 animate-pulse rounded-xl bg-muted" />
      ) : (
        <ul className="space-y-2">
          {q.data?.map((p) => (
            <LigneProduit key={p.id} p={p} />
          ))}
        </ul>
      )}
    </div>
  );
}

function LigneProduit({ p }: { p: Produit }) {
  const qc = useQueryClient();
  const [edite, setEdite] = useState(false);
  const [prix, setPrix] = useState(String(p.prix));
  const [confirme, setConfirme] = useState(false);

  const mTarif = useEcriture((_: void, cle) => tariferProduit(p.id, parseInt(prix, 10) || 0, cle), {
    onSuccess: () => {
      toast.success("Tarif consigné.");
      qc.invalidateQueries({ queryKey: ["produits", p.bar_id] });
      setEdite(false);
      setConfirme(false);
    },
    onError: (e) => {
      signalerErreur(e);
      setConfirme(false);
    },
  });
  const mRetrait = useEcriture((_: void, cle) => retirerProduit(p.id, cle), {
    onSuccess: () => {
      toast.success("Produit retiré de la vente.");
      qc.invalidateQueries({ queryKey: ["produits", p.bar_id] });
    },
    onError: signalerErreur,
  });

  return (
    <li className={cn("rounded-lg border bg-card p-3", !p.en_vente && "opacity-60")}>
      <div className="flex items-baseline justify-between gap-2">
        <div>
          <div className="font-semibold">{p.nom}</div>
          {!p.en_vente ? (
            <div className="text-[11px] text-muted-foreground">retiré de la vente</div>
          ) : null}
        </div>
        <Montant valeur={p.prix} taille="md" />
      </div>
      {edite ? (
        <div className="mt-3 space-y-2">
          <Label>Nouveau tarif</Label>
          <Input
            icone={Coins}
            inputMode="numeric"
            pattern="[0-9]*"
            value={prix}
            onChange={(e) => {
              setPrix(e.target.value.replace(/\D/g, ""));
              setConfirme(false);
            }}
          />
          {confirme ? (
            <div className="rounded-md bg-muted p-2 text-xs">
              Nouveau tarif : <Montant valeur={parseInt(prix, 10) || 0} taille="sm" />. Les ventes
              déjà saisies gardent leur prix.
            </div>
          ) : null}
          <div className="flex gap-2">
            <Button
              className="flex-1"
              disabled={mTarif.isPending}
              onClick={() => (confirme ? mTarif.mutate() : setConfirme(true))}
            >
              {mTarif.isPending ? "…" : confirme ? "Confirmer" : "Modifier"}
            </Button>
            <Button variant="outline" onClick={() => setEdite(false)}>
              Annuler
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={() => setEdite(true)}>
            Changer le tarif
          </Button>
          {p.en_vente ? (
            <Button
              size="sm"
              variant="ghost"
              disabled={mRetrait.isPending}
              onClick={() => mRetrait.mutate()}
            >
              {mRetrait.isPending ? "…" : "Retirer de la vente"}
            </Button>
          ) : null}
        </div>
      )}
    </li>
  );
}
