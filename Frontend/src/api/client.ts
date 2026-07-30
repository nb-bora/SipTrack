// Client HTTP unique pour l'API SipTrack.
// Toutes les URLs se terminent par un slash. Auth : `Token <jeton>` (jamais Bearer).
// Toute écriture porte un Idempotency-Key UUID v4, réutilisé en cas de réessai.

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, "") ?? "";

export class ErreurAPI extends Error {
  constructor(
    message: string,
    public statut: number,
    public detail?: string,
    public champs?: Record<string, string[]>,
  ) {
    super(message);
  }
}
export class ErreurValidation extends ErreurAPI {}
export class NonAuthentifie extends ErreurAPI {}
export class AccesRefuse extends ErreurAPI {}
export class Introuvable extends ErreurAPI {}
export class Conflit extends ErreurAPI {}
export class CleReutilisee extends ErreurAPI {}
export class TropDeRequetes extends ErreurAPI {}
export class PanneServeur extends ErreurAPI {}
export class PanneReseau extends ErreurAPI {
  constructor() {
    super("Le service est injoignable. Vérifiez votre connexion.", 0);
  }
}

export function uuidV4(): string {
  const c = (globalThis as { crypto?: Crypto }).crypto;
  if (c && typeof c.randomUUID === "function") return c.randomUUID();
  const b = new Uint8Array(16);
  (c ?? (globalThis as unknown as { crypto: Crypto }).crypto).getRandomValues(b);
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = Array.from(b, (x) => x.toString(16).padStart(2, "0"));
  return `${h.slice(0, 4).join("")}-${h.slice(4, 6).join("")}-${h.slice(6, 8).join("")}-${h.slice(8, 10).join("")}-${h.slice(10, 16).join("")}`;
}

const CLE_JETON = "siptrack.jeton";
export function lireJeton(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(CLE_JETON);
}
export function ecrireJeton(t: string) {
  localStorage.setItem(CLE_JETON, t);
}
export function purgerJeton() {
  localStorage.removeItem(CLE_JETON);
}

function url(chemin: string): string {
  const c = chemin.startsWith("/") ? chemin : `/${chemin}`;
  // Le slash final se pose sur le *chemin*, jamais après la requête : sinon
  // `?bar_id=abc` devenait `?bar_id=abc/` et le serveur cherchait un autre bar.
  const coupe = c.indexOf("?");
  const base = coupe === -1 ? c : c.slice(0, coupe);
  const requete = coupe === -1 ? "" : c.slice(coupe);
  const avecSlash = base.endsWith("/") ? base : `${base}/`;
  return `${BASE}${avecSlash}${requete}`;
}

async function traiterReponse<T>(rep: Response): Promise<T> {
  if (rep.status === 204) return undefined as T;
  const texte = await rep.text();
  let corps: unknown = null;
  if (texte) {
    try {
      corps = JSON.parse(texte);
    } catch {
      corps = texte;
    }
  }
  if (rep.ok) return corps as T;

  const detail = extraireDetail(corps);
  const champs = extraireChamps(corps);
  const message = detail ?? "Une erreur est survenue.";
  switch (rep.status) {
    case 400:
      throw new ErreurValidation(message, 400, detail, champs);
    case 401:
      purgerJeton();
      // Le jeton ne vaut plus rien : le bar retenu localement non plus.
      if (typeof localStorage !== "undefined") localStorage.removeItem("siptrack.barCourant");
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/connexion")) {
        window.location.assign("/connexion");
      }
      throw new NonAuthentifie(message, 401, detail);
    case 403:
      throw new AccesRefuse(message, 403, detail);
    case 404:
      throw new Introuvable(message, 404, detail);
    case 409:
      throw new Conflit(message, 409, detail);
    case 422:
      throw new CleReutilisee(message, 422, detail);
    case 429:
      throw new TropDeRequetes(message, 429, detail);
    default:
      if (rep.status >= 500) throw new PanneServeur(message, rep.status, detail);
      throw new ErreurAPI(message, rep.status, detail);
  }
}

function extraireDetail(corps: unknown): string | undefined {
  if (corps && typeof corps === "object" && "detail" in corps) {
    const d = (corps as Record<string, unknown>).detail;
    if (typeof d === "string") return d;
  }
  if (corps && typeof corps === "object" && "non_field_errors" in corps) {
    const n = (corps as Record<string, unknown>).non_field_errors;
    if (Array.isArray(n) && typeof n[0] === "string") return n[0] as string;
  }
  return undefined;
}
function extraireChamps(corps: unknown): Record<string, string[]> | undefined {
  if (!corps || typeof corps !== "object") return undefined;
  const o = corps as Record<string, unknown>;
  const r: Record<string, string[]> = {};
  for (const [k, v] of Object.entries(o)) {
    if (k === "detail") continue;
    if (Array.isArray(v) && v.every((x) => typeof x === "string")) r[k] = v as string[];
  }
  return Object.keys(r).length ? r : undefined;
}

function entetes(auth: boolean, cle?: string, contentType = "application/json"): HeadersInit {
  const h: Record<string, string> = { Accept: "application/json" };
  if (contentType) h["Content-Type"] = contentType;
  if (auth) {
    const j = lireJeton();
    if (j) h["Authorization"] = `Token ${j}`;
  }
  if (cle) h["Idempotency-Key"] = cle;
  return h;
}

async function envoyer(entree: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(entree, init);
  } catch {
    throw new PanneReseau();
  }
}

export async function lire<T = unknown>(chemin: string, opts: { auth?: boolean } = {}): Promise<T> {
  const auth = opts.auth ?? true;
  const rep = await envoyer(url(chemin), { method: "GET", headers: entetes(auth, undefined) });
  return traiterReponse<T>(rep);
}

type MethodeEcriture = "POST" | "PUT" | "PATCH" | "DELETE";

export interface OptsEcriture {
  cle?: string; // UUID v4 réutilisable pour retry
  auth?: boolean;
}

export async function ecrire<T = unknown>(
  methode: MethodeEcriture,
  chemin: string,
  corps?: unknown,
  opts: OptsEcriture = {},
): Promise<T> {
  const auth = opts.auth ?? true;
  const cle = opts.cle ?? uuidV4();
  const cible = url(chemin);
  const body = corps === undefined ? undefined : JSON.stringify(corps);
  const init: RequestInit = {
    method: methode,
    headers: entetes(auth, cle),
    body,
  };

  let rep = await envoyer(cible, init);
  // Retry unique sur 409 « en cours » avec la même clé
  if (rep.status === 409) {
    const clone = rep.clone();
    const t = await clone.text();
    if (/en cours|already in progress|déjà en cours/i.test(t)) {
      await new Promise((r) => setTimeout(r, 1500));
      rep = await envoyer(cible, init);
    }
  }
  return traiterReponse<T>(rep);
}

/** Génère une clé stable côté composant (à mémoriser via useRef/useState). */
export function nouvelleCle(): string {
  return uuidV4();
}
