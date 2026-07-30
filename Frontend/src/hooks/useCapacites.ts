import type { Capacite } from "@/api/types";

// Aujourd'hui l'API ne dit pas ce que l'utilisatrice peut faire.
// Convention : tout est permis, le serveur tranche (403 traité normalement).
// Point d'extension unique : le jour où /api/moi/ existe, brancher ici.
export function useCapacites() {
  return {
    peut: (_c: Capacite) => true,
    connues: false,
  };
}
