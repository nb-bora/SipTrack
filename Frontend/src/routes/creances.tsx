import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { listerEncoursBar } from "@/api/endpoints";
import { useSession } from "@/etat/session";
import { Montant, TitrePage } from "@/components/ui-siptrack";
import { useMemo } from "react";

export const Route = createFileRoute("/creances")({
  head: () => ({
    meta: [
      { title: "Créances — SipTrack" },
      { name: "description", content: "Encours des clients." },
    ],
  }),
  component: PageCreances,
});

function PageCreances() {
  const { barId } = useSession();
  const q = useQuery({
    queryKey: ["encours-bar", barId],
    queryFn: () => listerEncoursBar(barId as string),
    enabled: !!barId,
  });
  const tries = useMemo(() => [...(q.data ?? [])].sort((a, b) => b.reste - a.reste), [q.data]);
  return (
    <div>
      <TitrePage titre="Créances" sous="Les clients dont toutes les dettes sont éteintes n'apparaissent pas." />
      {q.isLoading ? (
        <div className="h-24 animate-pulse rounded-xl bg-muted" />
      ) : tries.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
          Aucun encours.
        </p>
      ) : (
        <ul className="space-y-2">
          {tries.map((c) => (
            <li key={c.client_id}>
              <Link
                to="/creances/$clientId"
                params={{ clientId: c.client_id }}
                className="flex items-center justify-between rounded-lg border border-border bg-card p-4 hover:border-primary"
              >
                <div>
                  <div className="font-semibold">{c.client_nom}</div>
                  <div className="text-xs text-muted-foreground">
                    Dû <Montant valeur={c.total_du} taille="sm" /> · remboursé <Montant valeur={c.total_rembourse} taille="sm" />
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Reste</div>
                  <Montant valeur={c.reste} taille="lg" ton="manquant" />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
