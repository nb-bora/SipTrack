import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQueries, useQueryClient } from "@tanstack/react-query";
import { getAddition, ouvrirAddition } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import {
  ajouterAdditionLocale,
  lireAdditionsLocales,
  lireServiceCourant,
  retirerAdditionLocale,
} from "@/etat/local";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Montant, TitrePage } from "@/components/ui-siptrack";
import { signalerErreur } from "@/domaine/erreurs";
import { toast } from "sonner";
import { Hash } from "lucide-react";

export const Route = createFileRoute("/tables")({
  head: () => ({
    meta: [
      { title: "Tables ouvertes — SipTrack" },
      { name: "description", content: "Additions ouvertes." },
    ],
  }),
  component: PageTables,
});

function PageTables() {
  const { barId } = useSession();
  const nav = useNavigate();
  const qc = useQueryClient();
  const serviceId = barId ? lireServiceCourant(barId) : null;
  const [tick, setTick] = useState(0);
  const [table, setTable] = useState("");

  // `tick` n'est pas lu dans le corps : c'est un signal d'invalidation. La
  // source est le localStorage, que React ne sait pas observer ; `setTick` est
  // appelé après chaque écriture pour forcer la relecture. La règle le croit
  // superflu — le retirer laisserait la liste périmée après l'ouverture d'une
  // table.
  const locales = useMemo(
    () => (serviceId ? lireAdditionsLocales(serviceId) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [serviceId, tick],
  );

  const details = useQueries({
    queries: locales.map((a) => ({
      queryKey: ["addition", serviceId, a.id],
      queryFn: () => getAddition(serviceId as string, a.id),
      enabled: !!serviceId,
      retry: false,
    })),
  });

  // Nettoyage des additions qui ne sont plus ouvertes.
  // `details` change d'identité à chaque rendu : on dépend d'une signature des
  // seuls statuts, sans quoi l'effet se rejouerait sans fin de raison.
  const statuts = details.map((d) => d.data?.statut ?? "?").join(",");
  useEffect(() => {
    if (!serviceId) return;
    const aRetirer = locales.filter((_, i) => {
      const s = details[i]?.data?.statut;
      return s !== undefined && s !== "ouverte";
    });
    if (aRetirer.length === 0) return;
    for (const a of aRetirer) retirerAdditionLocale(serviceId, a.id);
    setTick((t) => t + 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statuts, serviceId]);

  const m = useEcriture((n: number, cle) => ouvrirAddition(serviceId as string, n, cle), {
    onSuccess: (a) => {
      ajouterAdditionLocale(serviceId as string, { id: a.id, table_numero: a.table_numero });
      setTable("");
      setTick((t) => t + 1);
      qc.invalidateQueries({ queryKey: ["addition"] });
      toast.success(`Table ${a.table_numero} ouverte.`);
      nav({ to: "/tables/$aid", params: { aid: a.id } });
    },
    onError: signalerErreur,
  });

  if (!serviceId) {
    return (
      <div>
        <TitrePage titre="Tables" />
        <p className="text-sm text-muted-foreground">Aucun service en cours.</p>
      </div>
    );
  }

  return (
    <div>
      <TitrePage
        titre="Tables ouvertes"
        sous="Seules les tables ouvertes depuis cet appareil apparaissent ici."
      />
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const n = parseInt(table, 10);
          if (Number.isFinite(n) && n > 0) m.mutate(n);
        }}
        className="mb-4 flex gap-2"
      >
        <Input
          icone={Hash}
          inputMode="numeric"
          pattern="[0-9]*"
          placeholder="N° de table"
          value={table}
          onChange={(e) => setTable(e.target.value.replace(/\D/g, ""))}
        />
        <Button type="submit" disabled={m.isPending || !table}>
          {m.isPending ? "…" : "Ouvrir une table"}
        </Button>
      </form>

      {locales.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
          Aucune table ouverte depuis cet appareil.
        </p>
      ) : (
        <ul className="space-y-2">
          {locales.map((a, i) => {
            const d = details[i].data;
            return (
              <li key={a.id}>
                <Link
                  to="/tables/$aid"
                  params={{ aid: a.id }}
                  className="flex items-center justify-between rounded-lg border border-border bg-card p-4 hover:border-primary"
                >
                  <div>
                    <div className="font-semibold">Table {a.table_numero}</div>
                    <div className="text-xs text-muted-foreground">
                      {d ? `${d.lignes.length} ligne(s)` : "Chargement…"}
                    </div>
                  </div>
                  {d ? (
                    <div className="text-right">
                      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        Reste
                      </div>
                      <Montant
                        valeur={d.reste_a_payer}
                        taille="lg"
                        ton={d.reste_a_payer === 0 ? "solde" : "manquant"}
                      />
                    </div>
                  ) : null}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
