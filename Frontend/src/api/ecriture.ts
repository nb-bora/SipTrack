// Toute écriture passe par ici, pour une seule raison : la clé d'idempotence.
//
// Le backend exige un `Idempotency-Key` sur chaque écriture, et il s'en sert pour
// que deux envois de la *même* intention ne produisent qu'un seul Fait. Cette
// protection ne vaut que si la clé est **stable tant que l'intention n'a pas
// abouti**. Une clé tirée à chaque appel — ce que fait `ecrire()` par défaut —
// transforme un simple réessai en doublon, et le journal étant immuable, ce
// doublon ne se défait pas.
//
// La règle appliquée ici : une clé naît avec le formulaire, sert à tous les
// réessais, et n'est renouvelée qu'une fois l'écriture réellement aboutie.
//
// Un échec côté serveur libère la clé (le middleware la supprime sur toute
// réponse non-2xx) : la réutiliser après un refus est donc sans danger, même si
// l'utilisatrice a corrigé sa saisie entre-temps. Le seul cas où elle reste
// prise est le succès — précisément celui où l'on en tire une nouvelle.

import { useRef } from "react";
import { useMutation, type UseMutationResult } from "@tanstack/react-query";
import { uuidV4 } from "./client";

export interface OptionsEcriture<TDonnees, TVars> {
  onSuccess?: (donnees: TDonnees, variables: TVars) => void;
  onError?: (erreur: unknown, variables: TVars) => void;
}

/**
 * `useMutation` pour une écriture SipTrack.
 *
 * `ecriture` reçoit la clé en second argument et doit la transmettre au wrapper
 * d'endpoint. Ne pas la transmettre revient à retomber sur une clé jetable.
 */
export function useEcriture<TDonnees, TVars = void>(
  ecriture: (variables: TVars, cle: string) => Promise<TDonnees>,
  options: OptionsEcriture<TDonnees, TVars> = {},
): UseMutationResult<TDonnees, unknown, TVars> {
  const cle = useRef<string | null>(null);
  if (cle.current === null) cle.current = uuidV4();

  return useMutation<TDonnees, unknown, TVars>({
    // Aucun réessai automatique : le client HTTP en fait déjà un, ciblé, sur le
    // seul 409 « requête identique en cours ». Réessayer ici en aveugle
    // masquerait un refus métier derrière une attente.
    retry: false,
    mutationFn: (variables) => ecriture(variables, cle.current as string),
    onSuccess: (donnees, variables) => {
      // L'intention est consommée : la suivante mérite sa propre clé.
      cle.current = uuidV4();
      options.onSuccess?.(donnees, variables);
    },
    onError: options.onError,
  });
}
