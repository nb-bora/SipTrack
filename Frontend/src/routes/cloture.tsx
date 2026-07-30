import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { cloturerService, getService, listerSousCaisses } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { ecrireServiceCourant, lireAdditionsLocales, lireServiceCourant } from "@/etat/local";
import { Button } from "@/components/ui/button";
import { LigneKV, Montant, TitrePage } from "@/components/ui-siptrack";
import { LIBELLE_STATUT_SERVICE } from "@/domaine/libelles";
import { signalerErreur } from "@/domaine/erreurs";
import { toast } from "sonner";
import { useState } from "react";

export const Route = createFileRoute("/cloture")({
  head: () => ({
    meta: [
      { title: "Clôturer le service — SipTrack" },
      { name: "description", content: "Récapitulatif et clôture." },
    ],
  }),
  component: PageCloture,
});

function PageCloture() {
  const { barId } = useSession();
  const nav = useNavigate();
  const qc = useQueryClient();
  const serviceId = barId ? lireServiceCourant(barId) : null;
  const [confirme, setConfirme] = useState(false);

  const service = useQuery({
    queryKey: ["service", serviceId],
    queryFn: () => getService(serviceId as string),
    enabled: !!serviceId,
  });
  const sc = useQuery({
    queryKey: ["sous-caisses", serviceId],
    queryFn: () => listerSousCaisses(serviceId as string),
    enabled: !!serviceId,
  });

  const m = useEcriture((_: void, cle) => cloturerService(serviceId as string, cle), {
    onSuccess: () => {
      toast.success("Service clôturé.");
      ecrireServiceCourant(barId as string, null);
      qc.invalidateQueries({ queryKey: ["service"] });
      nav({ to: "/accueil" });
    },
    onError: (e) => {
      signalerErreur(e);
      setConfirme(false);
    },
  });

  if (!serviceId) return <p className="text-sm text-muted-foreground">Aucun service en cours.</p>;

  const additionsLocales = lireAdditionsLocales(serviceId);

  return (
    <div>
      <TitrePage titre="Clôturer le service" />
      {service.data ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <LigneKV k="Statut" v={LIBELLE_STATUT_SERVICE[service.data.statut]} />
          <LigneKV k="Fond de caisse" v={<Montant valeur={service.data.fond_de_caisse} />} />
        </div>
      ) : null}

      {additionsLocales.length > 0 ? (
        <div className="mt-4 rounded-md border border-attente/40 bg-attente/10 p-3 text-sm text-attente">
          {additionsLocales.length} table(s) semblent encore ouvertes depuis cet appareil. Réglez-les d'abord.
        </div>
      ) : null}

      <h2 className="mt-6 mb-2 text-sm uppercase tracking-wide text-muted-foreground">
        Sous-caisses
      </h2>
      <div className="overflow-x-auto rounded-xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2">Serveuse</th>
              <th className="px-3 py-2 text-right">Espèces</th>
              <th className="px-3 py-2 text-right">Mob.&nbsp;money</th>
              <th className="px-3 py-2 text-right">Versé</th>
              <th className="px-3 py-2 text-right">Écart</th>
            </tr>
          </thead>
          <tbody>
            {sc.data?.map((x) => (
              <tr key={x.serveuse_id} className="border-t border-border">
                <td className="px-3 py-2">{x.serveuse_id.slice(0, 8)}</td>
                <td className="px-3 py-2 text-right montant">{x.encaisse_especes.toLocaleString("fr-FR")}</td>
                <td className="px-3 py-2 text-right montant">{x.encaisse_mobile_money.toLocaleString("fr-FR")}</td>
                <td className="px-3 py-2 text-right">
                  {x.verse === null ? <span className="text-attente">en&nbsp;attente</span> : <span className="montant">{x.verse.toLocaleString("fr-FR")}</span>}
                </td>
                <td className="px-3 py-2 text-right">
                  {x.ecart === null ? (
                    <span className="text-attente">—</span>
                  ) : (
                    <span
                      className={
                        "montant " +
                        (x.ecart === 0 ? "text-solde" : x.ecart > 0 ? "text-attente" : "text-manquant")
                      }
                    >
                      {x.ecart.toLocaleString("fr-FR")}
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {sc.data && sc.data.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-muted-foreground">
                  Aucune sous-caisse.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <Button
        className="mt-6 h-12 w-full text-base"
        variant={confirme ? "destructive" : "default"}
        disabled={m.isPending}
        onClick={() => (confirme ? m.mutate() : setConfirme(true))}
      >
        {m.isPending
          ? "Clôture…"
          : confirme
          ? "Confirmer la clôture (irréversible)"
          : "Clôturer le service"}
      </Button>
    </div>
  );
}
