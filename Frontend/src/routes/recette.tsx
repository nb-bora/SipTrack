import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listerSousCaisses, verserRecette } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { lireServiceCourant } from "@/etat/local";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LigneKV, Montant, TitrePage } from "@/components/ui-siptrack";
import { signalerErreur } from "@/domaine/erreurs";
import { toast } from "sonner";

export const Route = createFileRoute("/recette")({
  head: () => ({
    meta: [
      { title: "Verser ma recette — SipTrack" },
      { name: "description", content: "Remise en caisse des espèces encaissées." },
    ],
  }),
  component: PageRecette,
});

function PageRecette() {
  const { barId } = useSession();
  const serviceId = barId ? lireServiceCourant(barId) : null;
  const qc = useQueryClient();
  const [montant, setMontant] = useState("");
  const [confirme, setConfirme] = useState(false);

  const sc = useQuery({
    queryKey: ["sous-caisses", serviceId],
    queryFn: () => listerSousCaisses(serviceId as string),
    enabled: !!serviceId,
  });

  // On ne connaît pas l'identifiant de la serveuse ici : on ne peut donc pas afficher
  // l'attendu personnel. On affiche l'ensemble des sous-caisses en information.
  const totalEspecesAttendu = useMemo(
    () => sc.data?.reduce((s, x) => s + x.encaisse_especes, 0) ?? null,
    [sc.data],
  );

  const m = useEcriture((n: number, cle) => verserRecette(serviceId as string, n, cle), {
    onSuccess: (v) => {
      toast.success("Recette versée.");
      qc.invalidateQueries({ queryKey: ["sous-caisses", serviceId] });
      setDernier(v);
      setConfirme(false);
    },
    onError: (e) => {
      signalerErreur(e);
      setConfirme(false);
    },
  });

  const [dernier, setDernier] = useState<null | { attendu: number; verse: number; ecart: number }>(null);

  if (!serviceId) return <p className="text-sm text-muted-foreground">Aucun service en cours.</p>;

  const n = parseInt(montant || "0", 10) || 0;

  return (
    <div>
      <TitrePage
        titre="Verser ma recette"
        sous="Vous versez la somme en espèces que vous avez encaissée sur ce service. Le mobile money ne se remet pas de la main à la main."
      />

      <p className="mb-4 rounded-md border border-attente/40 bg-attente/10 p-3 text-xs text-attente">
        L'attendu est calculé sur vos <strong>encaissements de tables</strong> uniquement. Les ventes
        au comptoir, elles, ne sont pas comptées dans ce montant.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!confirme) {
            setConfirme(true);
            return;
          }
          if (n > 0) m.mutate(n);
        }}
        className="rounded-xl border border-border bg-card p-4"
      >
        <Label htmlFor="m">Montant remis en caisse (FCFA)</Label>
        <Input
          id="m"
          inputMode="numeric"
          pattern="[0-9]*"
          value={montant}
          onChange={(e) => {
            setMontant(e.target.value.replace(/\D/g, ""));
            setConfirme(false);
          }}
          required
        />
        {confirme ? (
          <div className="mt-3 rounded-md bg-muted p-3 text-sm">
            Confirmez-vous verser <Montant valeur={n} taille="md" /> ?
          </div>
        ) : null}
        <Button type="submit" className="mt-4 h-12 w-full text-base" disabled={m.isPending || n <= 0}>
          {m.isPending ? "Versement…" : confirme ? "Confirmer le versement" : "Verser"}
        </Button>
        <p className="mt-2 text-[11px] text-muted-foreground">
          Un second versement sur ce service sera refusé par le serveur.
        </p>
      </form>

      {dernier ? (
        <div className="mt-4 rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 font-semibold">Résultat du versement</h2>
          <LigneKV k="Attendu" v={<Montant valeur={dernier.attendu} taille="md" />} />
          <LigneKV k="Versé" v={<Montant valeur={dernier.verse} taille="md" />} />
          <LigneKV
            k="Écart"
            v={
              <Montant
                valeur={dernier.ecart}
                taille="lg"
                ton={dernier.ecart === 0 ? "solde" : dernier.ecart > 0 ? "attente" : "manquant"}
              />
            }
          />
          <p className="mt-2 text-xs text-muted-foreground">
            Un écart est un fait consigné, pas une accusation.
          </p>
        </div>
      ) : null}

      <div className="mt-6">
        <h2 className="mb-2 text-sm uppercase tracking-wide text-muted-foreground">
          Sous-caisses du service
        </h2>
        {sc.isLoading ? (
          <div className="h-24 animate-pulse rounded-lg bg-muted" />
        ) : sc.data && sc.data.length > 0 ? (
          <ul className="space-y-2">
            {sc.data.map((x) => (
              <li key={x.serveuse_id} className="rounded-lg border border-border bg-card p-3 text-sm">
                <div className="mb-1 text-xs text-muted-foreground">Serveuse : {x.serveuse_id.slice(0, 8)}</div>
                <LigneKV k="Encaissé espèces" v={<Montant valeur={x.encaisse_especes} />} />
                <LigneKV k="Encaissé mobile money" v={<Montant valeur={x.encaisse_mobile_money} />} />
                <LigneKV
                  k="Versé"
                  v={x.verse === null ? <span className="text-attente">en attente</span> : <Montant valeur={x.verse} />}
                />
                <LigneKV
                  k="Écart"
                  v={
                    x.ecart === null ? (
                      <span className="text-attente">en attente</span>
                    ) : (
                      <Montant
                        valeur={x.ecart}
                        ton={x.ecart === 0 ? "solde" : x.ecart > 0 ? "attente" : "manquant"}
                      />
                    )
                  }
                />
              </li>
            ))}
            <li className="pt-2 text-right text-xs text-muted-foreground">
              Total encaissé en espèces sur les tables :{" "}
              <Montant valeur={totalEspecesAttendu} taille="sm" />
            </li>
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Aucune sous-caisse pour ce service.</p>
        )}
      </div>
    </div>
  );
}
