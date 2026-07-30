import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEcriture } from "@/api/ecriture";
import {
  encaisserPaiement,
  enregistrerVente,
  getAddition,
  listerProduits,
  reglerAddition,
  creerClient,
  listerEncoursBar,
} from "@/api/endpoints";
import { useSession } from "@/etat/session";
import { lireServiceCourant, retirerAdditionLocale } from "@/etat/local";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LigneKV, Montant, TitrePage } from "@/components/ui-siptrack";
import { LIBELLE_FORME, LIBELLE_STATUT_ADDITION } from "@/domaine/libelles";
import type { FormePaiement, Produit } from "@/api/types";
import { signalerErreur } from "@/domaine/erreurs";
import { toast } from "sonner";
import { formatHeure } from "@/domaine/format";
import { cn } from "@/lib/utils";
import { Coins, User } from "lucide-react";

export const Route = createFileRoute("/tables/$aid")({
  head: () => ({
    meta: [
      { title: "Détail d'une addition — SipTrack" },
      { name: "description", content: "Consommations, encaissements, reste à payer." },
    ],
  }),
  component: PageAddition,
});

function PageAddition() {
  const { aid } = Route.useParams();
  const { barId } = useSession();
  const nav = useNavigate();
  const qc = useQueryClient();
  const serviceId = barId ? lireServiceCourant(barId) : null;

  const rq = useQuery({
    queryKey: ["addition", serviceId, aid],
    queryFn: () => getAddition(serviceId as string, aid),
    enabled: !!serviceId,
  });

  const [mode, setMode] = useState<"aucun" | "ajout" | "paiement">("aucun");

  if (!serviceId) return <p className="text-sm text-muted-foreground">Aucun service en cours.</p>;
  if (rq.isLoading) return <div className="h-40 animate-pulse rounded-xl bg-muted" />;
  if (rq.isError || !rq.data) return <p className="text-sm text-manquant">Addition introuvable.</p>;

  const a = rq.data;
  const soldee = a.reste_a_payer === 0;

  return (
    <div>
      <TitrePage
        titre={`Table ${a.table_numero}`}
        sous={`Ouverte à ${formatHeure(a.ouvert_le)} · ${LIBELLE_STATUT_ADDITION[a.statut]}`}
      />

      <div className="rounded-xl border border-border bg-card p-4">
        <LigneKV k="Total" v={<Montant valeur={a.total} taille="lg" />} />
        <LigneKV k="Payé" v={<Montant valeur={a.paye} taille="md" ton="muted" />} />
        <div className="mt-2 flex items-baseline justify-between border-t border-border pt-3">
          <span className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Reste à payer</span>
          <Montant
            valeur={a.reste_a_payer}
            taille="xl"
            ton={soldee ? "solde" : "manquant"}
          />
        </div>
      </div>

      {a.lignes.length > 0 ? (
        <div className="mt-4 rounded-xl border border-border bg-card">
          <div className="border-b border-border px-4 py-2 text-xs uppercase tracking-wide text-muted-foreground">
            Consommations
          </div>
          <ul className="divide-y divide-border">
            {a.lignes.map((l) => (
              <li key={l.vente_id} className="flex items-baseline justify-between px-4 py-2 text-sm">
                <div>
                  <span className="montant font-semibold">{l.quantite}</span> × produit{" "}
                  <span className="text-muted-foreground">{l.produit_id.slice(0, 8)}</span>
                  <span className="ml-2 text-[11px] uppercase text-muted-foreground">
                    {LIBELLE_FORME[l.forme_paiement]}
                  </span>
                </div>
                <Montant valeur={l.montant_total} taille="md" />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {a.paiements.length > 0 ? (
        <div className="mt-4 rounded-xl border border-border bg-card">
          <div className="border-b border-border px-4 py-2 text-xs uppercase tracking-wide text-muted-foreground">
            Encaissements
          </div>
          <ul className="divide-y divide-border">
            {a.paiements.map((p) => (
              <li key={p.paiement_id} className="flex items-baseline justify-between px-4 py-2 text-sm">
                <span>
                  {formatHeure(p.horodatage)} · {LIBELLE_FORME[p.forme_paiement]}
                </span>
                <Montant valeur={p.montant} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {a.statut === "ouverte" ? (
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Button
            variant={mode === "ajout" ? "default" : "outline"}
            className="h-12"
            onClick={() => setMode(mode === "ajout" ? "aucun" : "ajout")}
          >
            Ajouter une consommation
          </Button>
          <Button
            variant={mode === "paiement" ? "default" : "outline"}
            className="h-12"
            onClick={() => setMode(mode === "paiement" ? "aucun" : "paiement")}
            disabled={soldee}
          >
            Encaisser
          </Button>
        </div>
      ) : null}

      {mode === "ajout" ? <FormAjoutConso serviceId={serviceId} additionId={aid} /> : null}
      {mode === "paiement" && !soldee ? (
        <FormPaiement serviceId={serviceId} barId={barId as string} additionId={aid} reste={a.reste_a_payer} />
      ) : null}

      {soldee && a.statut === "ouverte" ? (
        <RegleAddition serviceId={serviceId} additionId={aid} onFait={() => {
          retirerAdditionLocale(serviceId, aid);
          qc.invalidateQueries({ queryKey: ["addition"] });
          nav({ to: "/tables" });
        }} />
      ) : null}
    </div>
  );
}

function FormAjoutConso({ serviceId, additionId }: { serviceId: string; additionId: string }) {
  const { barId } = useSession();
  const qc = useQueryClient();
  const [sel, setSel] = useState<Produit | null>(null);
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
        serviceId,
        {
          produit_id: sel!.id,
          quantite: q,
          forme_paiement: forme,
          addition_id: additionId,
        },
        cle,
      ),
    {
      onSuccess: () => {
        toast.success("Consommation ajoutée.");
        qc.invalidateQueries({ queryKey: ["addition", serviceId, additionId] });
        setSel(null);
        setQ(1);
      },
      onError: signalerErreur,
    },
  );
  return (
    <div className="mt-3 rounded-xl border border-border bg-card p-3">
      <div className="grid grid-cols-2 gap-2">
        {produits.map((p) => (
          <button
            key={p.id}
            onClick={() => setSel(p)}
            className={cn(
              "flex min-h-[72px] flex-col items-start justify-between rounded-md border-2 p-2 text-left",
              sel?.id === p.id ? "border-primary" : "border-border",
            )}
          >
            <span className="text-sm font-semibold">{p.nom}</span>
            <Montant valeur={p.prix} taille="sm" />
          </button>
        ))}
      </div>
      {sel ? (
        <div className="mt-3 space-y-3">
          <div className="flex items-center gap-2">
            <Button variant="outline" className="h-10 w-10 p-0" onClick={() => setQ((x) => Math.max(1, x - 1))}>−</Button>
            <span className="montant w-8 text-center text-lg font-bold">{q}</span>
            <Button variant="outline" className="h-10 w-10 p-0" onClick={() => setQ((x) => x + 1)}>+</Button>
            <span className="ml-auto"><Montant valeur={sel.prix * q} taille="md" /></span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {(Object.keys(LIBELLE_FORME) as FormePaiement[]).map((f) => (
              <button
                key={f}
                onClick={() => setForme(f)}
                className={cn(
                  "min-h-[44px] rounded-md border-2 px-2 text-xs",
                  forme === f ? "border-primary text-primary" : "border-border",
                )}
              >
                {LIBELLE_FORME[f]}
              </button>
            ))}
          </div>
          <Button className="h-12 w-full" disabled={m.isPending} onClick={() => m.mutate()}>
            {m.isPending ? "Ajout…" : "Ajouter"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

function FormPaiement({
  serviceId,
  barId,
  additionId,
  reste,
}: {
  serviceId: string;
  barId: string;
  additionId: string;
  reste: number;
}) {
  const qc = useQueryClient();
  const [montant, setMontant] = useState(String(reste));
  const [forme, setForme] = useState<FormePaiement>("especes");
  const [clientNom, setClientNom] = useState("");
  const [clientId, setClientId] = useState<string | null>(null);

  const clientsQ = useQuery({
    queryKey: ["encours-bar", barId],
    queryFn: () => listerEncoursBar(barId),
    enabled: forme === "credit",
  });

  // Le serveur est idempotent sur le nom : un nom déjà connu dans ce bar rend le
  // client existant. Ce bouton retrouve donc autant qu'il crée.
  const mCreerClient = useEcriture((_: void, cle) => creerClient(barId, clientNom.trim(), cle), {
    onSuccess: (c) => {
      setClientId(c.id);
      toast.success(`Client « ${c.nom} » sélectionné.`);
      qc.invalidateQueries({ queryKey: ["encours-bar", barId] });
    },
    onError: signalerErreur,
  });

  const m = useEcriture(
    (_: void, cle) => {
      const n = Math.min(parseInt(montant || "0", 10) || 0, reste);
      return encaisserPaiement(
        serviceId,
        additionId,
        {
          montant: n,
          forme_paiement: forme,
          client_id: forme === "credit" ? clientId ?? undefined : undefined,
        },
        cle,
      );
    },
    {
      onSuccess: () => {
        toast.success("Paiement enregistré.");
        qc.invalidateQueries({ queryKey: ["addition", serviceId, additionId] });
      },
      onError: signalerErreur,
    },
  );

  const n = Math.min(parseInt(montant || "0", 10) || 0, reste);
  const bloqueCredit = forme === "credit" && !clientId;

  return (
    <div className="mt-3 rounded-xl border border-border bg-card p-3 space-y-3">
      <div>
        <Label>Montant à encaisser</Label>
        <Input
          icone={Coins}
          inputMode="numeric"
          pattern="[0-9]*"
          value={montant}
          onChange={(e) => setMontant(e.target.value.replace(/\D/g, ""))}
        />
        <p className="mt-1 text-xs text-muted-foreground">Reste à payer : <Montant valeur={reste} taille="sm" /></p>
      </div>
      <div>
        <Label>Forme de paiement</Label>
        <div className="mt-1 grid grid-cols-3 gap-2">
          {(Object.keys(LIBELLE_FORME) as FormePaiement[]).map((f) => (
            <button
              key={f}
              onClick={() => setForme(f)}
              className={cn(
                "min-h-[44px] rounded-md border-2 px-2 text-xs",
                forme === f ? "border-primary text-primary" : "border-border",
              )}
            >
              {LIBELLE_FORME[f]}
            </button>
          ))}
        </div>
      </div>
      {forme === "credit" ? (
        <div className="rounded-md border border-attente/40 bg-attente/10 p-3">
          <p className="text-xs text-attente">
            Un paiement en crédit solde l'addition sans qu'aucun argent n'entre. Une créance sera ouverte au nom du client.
          </p>
          <div className="mt-2 space-y-2">
            <Label>Client</Label>
            <select
              className="h-11 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={clientId ?? ""}
              onChange={(e) => setClientId(e.target.value || null)}
            >
              <option value="">— Aucun client sélectionné —</option>
              {clientsQ.data?.map((c) => (
                <option key={c.client_id} value={c.client_id}>
                  {c.client_nom}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-muted-foreground">
              Cette liste ne montre que les clients ayant une dette en cours. Pour tout autre client,
              saisissez son nom ci-dessous : un nom déjà connu du bar sera retrouvé, pas dupliqué.
            </p>
            <div className="flex gap-2">
              <Input
                icone={User}
                placeholder="Nom du client"
                value={clientNom}
                onChange={(e) => setClientNom(e.target.value)}
              />
              <Button
                variant="outline"
                disabled={mCreerClient.isPending || !clientNom.trim()}
                onClick={() => mCreerClient.mutate()}
              >
                {mCreerClient.isPending ? "…" : "Retrouver ou créer"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
      <div className="rounded-md bg-muted p-3">
        <div className="text-xs text-muted-foreground">Récapitulatif</div>
        <div className="mt-1 flex items-baseline justify-between">
          <span className="text-sm">{LIBELLE_FORME[forme]}</span>
          <Montant valeur={n} taille="lg" />
        </div>
      </div>
      <Button className="h-12 w-full" disabled={m.isPending || n <= 0 || bloqueCredit} onClick={() => m.mutate()}>
        {m.isPending ? "Encaissement…" : "Confirmer l'encaissement"}
      </Button>
    </div>
  );
}

function RegleAddition({ serviceId, additionId, onFait }: { serviceId: string; additionId: string; onFait: () => void }) {
  const m = useEcriture((_: void, cle) => reglerAddition(serviceId, additionId, cle), {
    onSuccess: () => {
      toast.success("Addition réglée.");
      onFait();
    },
    onError: signalerErreur,
  });
  return (
    <div className="mt-4 rounded-xl border border-solde/40 bg-solde/10 p-4">
      <p className="text-sm text-solde">Le reste à payer atteint 0. Vous pouvez constater le règlement.</p>
      <Button className="mt-3 h-12 w-full" disabled={m.isPending} onClick={() => m.mutate()}>
        {m.isPending ? "…" : "Régler l'addition"}
      </Button>
    </div>
  );
}
