import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { listerAcces } from "@/api/endpoints";
import { useSession } from "@/etat/session";
import { TitrePage } from "@/components/ui-siptrack";
import { formatDateHeure } from "@/domaine/format";

export const Route = createFileRoute("/journal-acces")({
  head: () => ({
    meta: [
      { title: "Consultations plateforme — SipTrack" },
      { name: "description", content: "Qui, hors du bar, a consulté vos données." },
    ],
  }),
  component: Page,
});

function Page() {
  const { barId } = useSession();
  const q = useQuery({
    queryKey: ["acces", barId],
    queryFn: () => listerAcces(barId as string),
    enabled: !!barId,
  });
  return (
    <div>
      <TitrePage titre="Consultations plateforme" sous="Qui, hors du bar, a consulté vos données." />
      {q.isLoading ? (
        <div className="h-24 animate-pulse rounded-xl bg-muted" />
      ) : q.data && q.data.length > 0 ? (
        <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
          {q.data.map((a, i) => (
            <li key={i} className="p-3 text-sm">
              <div className="flex items-baseline justify-between">
                <span className="font-medium">{a.operation}</span>
                <span className="text-xs text-muted-foreground">{formatDateHeure(a.horodatage)}</span>
              </div>
              <div className="mt-1 text-[11px] text-muted-foreground">Administrateur : {a.administrateur_id}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
          Aucune consultation enregistrée.
        </p>
      )}
    </div>
  );
}
