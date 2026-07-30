import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getService, ouvrirService } from "@/api/endpoints";
import { useEcriture } from "@/api/ecriture";
import { useSession } from "@/etat/session";
import { ecrireServiceCourant, lireServiceCourant } from "@/etat/local";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LigneKV, Montant, TitrePage } from "@/components/ui-siptrack";
import { signalerErreur } from "@/domaine/erreurs";
import { LIBELLE_STATUT_SERVICE } from "@/domaine/libelles";
import { formatDateHeure } from "@/domaine/format";
import { toast } from "sonner";
import { Coins, ClipboardList, ArrowUpToLine, Lock } from "lucide-react";

export const Route = createFileRoute("/accueil")({
  head: () => ({
    meta: [
      { title: "Service en cours — SipTrack" },
      { name: "description", content: "État du service courant, ventes et clôture." },
    ],
  }),
  component: PageAccueil,
});

function PageAccueil() {
  const { barId } = useSession();
  const nav = useNavigate();
  const qc = useQueryClient();
  const serviceId = barId ? lireServiceCourant(barId) : null;

  const [fond, setFond] = useState("");

  const q = useQuery({
    queryKey: ["service", serviceId],
    queryFn: () => getService(serviceId as string),
    enabled: !!serviceId,
    retry: false,
  });

  const m = useEcriture((n: number, cle) => ouvrirService(barId as string, n, cle), {
    onSuccess: (s) => {
      ecrireServiceCourant(barId as string, s.id);
      qc.invalidateQueries({ queryKey: ["service"] });
      toast.success("Service ouvert.");
    },
    onError: signalerErreur,
  });

  if (!barId) return <p className="text-sm text-muted-foreground">Choisissez d'abord un bar.</p>;

  const service = q.data;
  const enCours = service && service.statut === "ouvert";

  return (
    <div>
      <TitrePage titre="Service en cours" />
      {!serviceId || q.isError ? (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-lg font-semibold">Ouvrir un service</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Indiquez le fond de caisse laissé pour faire la monnaie.
          </p>
          <form
            className="mt-4 space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              const n = parseInt(fond, 10);
              if (Number.isFinite(n) && n >= 0) m.mutate(n);
            }}
          >
            <div>
              <Label htmlFor="fond">Fond de caisse (FCFA)</Label>
              <Input
                id="fond"
                inputMode="numeric"
                pattern="[0-9]*"
                value={fond}
                onChange={(e) => setFond(e.target.value.replace(/\D/g, ""))}
                required
              />
            </div>
            <Button type="submit" disabled={m.isPending} className="h-12 w-full text-base">
              {m.isPending ? "Ouverture…" : "Ouvrir le service"}
            </Button>
          </form>
          <p className="mt-4 text-xs text-muted-foreground">
            Si un service est déjà en cours mais absent d'ici, saisissez son identifiant dans Réglages.
          </p>
        </div>
      ) : q.isLoading ? (
        <div className="h-40 animate-pulse rounded-xl bg-muted" />
      ) : service ? (
        <>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs uppercase tracking-wide text-muted-foreground">Statut</span>
              <span
                className={
                  "rounded-full px-2 py-0.5 text-xs font-medium " +
                  (enCours ? "bg-solde/15 text-solde" : "bg-muted text-muted-foreground")
                }
              >
                {LIBELLE_STATUT_SERVICE[service.statut]}
              </span>
            </div>
            <LigneKV k="Fond de caisse" v={<Montant valeur={service.fond_de_caisse} taille="lg" />} />
            <LigneKV k="Ouvert le" v={<span className="text-sm">{formatDateHeure(service.ouvert_le)}</span>} />
            {service.clos_le ? (
              <LigneKV k="Clos le" v={<span className="text-sm">{formatDateHeure(service.clos_le)}</span>} />
            ) : null}
            <p className="mt-3 text-[11px] text-muted-foreground">Service : {service.id}</p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <ActionCarte to="/vente" icon={Coins} titre="Vente rapide" />
            <ActionCarte to="/tables" icon={ClipboardList} titre="Tables" />
            <ActionCarte to="/recette" icon={ArrowUpToLine} titre="Verser ma recette" />
            <ActionCarte to="/cloture" icon={Lock} titre="Clôturer" />
          </div>

          {!enCours ? (
            <button
              onClick={() => {
                ecrireServiceCourant(barId, null);
                nav({ to: "/accueil" });
              }}
              className="mt-4 text-xs text-muted-foreground underline"
            >
              Ouvrir un nouveau service
            </button>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function ActionCarte({ to, icon: Icon, titre }: { to: string; icon: React.ComponentType<{ className?: string }>; titre: string }) {
  return (
    <Link
      to={to}
      className="flex min-h-[96px] flex-col items-start justify-between rounded-xl border border-border bg-card p-4 text-left hover:border-primary"
    >
      <Icon className="h-6 w-6 text-primary" />
      <span className="text-base font-semibold">{titre}</span>
    </Link>
  );
}
