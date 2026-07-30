// Traduction humaine des erreurs typées de l'API.
import { toast } from "sonner";
import {
  AccesRefuse,
  Conflit,
  CleReutilisee,
  ErreurAPI,
  ErreurValidation,
  Introuvable,
  NonAuthentifie,
  PanneReseau,
  PanneServeur,
  TropDeRequetes,
} from "@/api/client";

export function messageErreur(e: unknown): string {
  if (e instanceof PanneReseau) return "Le service est injoignable. Vérifiez votre connexion.";
  if (e instanceof TropDeRequetes) return "Trop de tentatives. Réessayez dans une minute.";
  if (e instanceof NonAuthentifie) return "Session expirée. Reconnectez-vous.";
  if (e instanceof AccesRefuse) return e.detail ?? "Vous n'avez pas la capacité pour cette action.";
  if (e instanceof Introuvable) return e.detail ?? "Élément introuvable.";
  if (e instanceof Conflit) return e.detail ?? "Action refusée par le serveur.";
  if (e instanceof CleReutilisee)
    return "Erreur technique : clé d'idempotence réutilisée. Rechargez la page.";
  if (e instanceof PanneServeur) return e.detail ?? "Le serveur a rencontré une erreur.";
  if (e instanceof ErreurValidation) {
    if (e.champs) {
      const p = Object.entries(e.champs)
        .map(([k, v]) => `${k} : ${v.join(", ")}`)
        .join(" · ");
      return p || e.detail || "Requête invalide.";
    }
    return e.detail ?? "Requête invalide.";
  }
  if (e instanceof ErreurAPI) return e.detail ?? e.message;
  if (e instanceof Error) return e.message;
  return "Erreur inconnue.";
}

export function signalerErreur(e: unknown) {
  toast.error(messageErreur(e));
}
