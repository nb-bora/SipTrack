import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { formatXAF } from "@/domaine/format";

/** Affichage de montant XAF, chiffres tabulaires, gros et lisibles. */
export function Montant({
  valeur,
  taille = "md",
  ton = "neutre",
  className,
}: {
  valeur: number | null | undefined;
  taille?: "sm" | "md" | "lg" | "xl";
  ton?: "neutre" | "solde" | "attente" | "manquant" | "muted";
  className?: string;
}) {
  const tailles = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-2xl font-semibold",
    xl: "text-4xl font-bold",
  }[taille];
  const tons = {
    neutre: "text-foreground",
    solde: "text-solde",
    attente: "text-attente",
    manquant: "text-manquant",
    muted: "text-muted-foreground",
  }[ton];
  return <span className={cn("montant", tailles, tons, className)}>{formatXAF(valeur ?? undefined)}</span>;
}

export function LigneKV({ k, v, className }: { k: ReactNode; v: ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-baseline justify-between gap-4 py-1.5", className)}>
      <span className="text-sm text-muted-foreground">{k}</span>
      <span>{v}</span>
    </div>
  );
}

export function TitrePage({ titre, sous }: { titre: string; sous?: string }) {
  return (
    <div className="mb-4">
      <h1 className="text-2xl font-bold tracking-tight">{titre}</h1>
      {sous ? <p className="mt-1 text-sm text-muted-foreground">{sous}</p> : null}
    </div>
  );
}
