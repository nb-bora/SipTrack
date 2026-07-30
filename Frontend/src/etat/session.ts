// État global minimal : jeton, bar courant. Le service courant est déduit via etat/local.
import { useSyncExternalStore } from "react";
import { ecrireJeton, lireJeton, purgerJeton } from "@/api/client";

const CLE_BAR = "siptrack.barCourant";

type Etat = { jeton: string | null; barId: string | null };

const abonnes = new Set<() => void>();
let etat: Etat = {
  jeton: typeof window === "undefined" ? null : lireJeton(),
  barId: typeof window === "undefined" ? null : localStorage.getItem(CLE_BAR),
};

function notifier() {
  for (const f of abonnes) f();
}
function abonner(f: () => void) {
  abonnes.add(f);
  return () => abonnes.delete(f);
}
function snapshot(): Etat {
  return etat;
}
const snapshotServeur: Etat = { jeton: null, barId: null };

export function useSession() {
  return useSyncExternalStore(abonner, snapshot, () => snapshotServeur);
}

export function definirJeton(j: string) {
  ecrireJeton(j);
  etat = { ...etat, jeton: j };
  notifier();
}
export function deconnecter() {
  purgerJeton();
  if (typeof localStorage !== "undefined") localStorage.removeItem(CLE_BAR);
  etat = { jeton: null, barId: null };
  notifier();
}
export function definirBar(id: string | null) {
  if (typeof localStorage !== "undefined") {
    if (id) localStorage.setItem(CLE_BAR, id);
    else localStorage.removeItem(CLE_BAR);
  }
  etat = { ...etat, barId: id };
  notifier();
}
