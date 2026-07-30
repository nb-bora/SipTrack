import type { Capacite, FormePaiement, StatutAddition, StatutService } from "@/api/types";

export const LIBELLE_CAPACITE: Record<Capacite, string> = {
  ouvrir_service: "Ouvrir un service",
  enregistrer_vente: "Enregistrer une vente",
  encaisser: "Encaisser un paiement",
  verser_recette: "Verser sa recette",
  cloturer_service: "Clôturer le service",
  creer_client: "Créer un client",
  accorder_credit: "Accorder un crédit",
  encaisser_remboursement: "Encaisser un remboursement",
  inscrire_produit: "Inscrire un produit au catalogue",
  tarifer: "Modifier un tarif",
  retirer_produit: "Retirer un produit de la vente",
  creer_compte: "Créer un compte",
  accorder_capacite: "Accorder une capacité",
  retirer_capacite: "Retirer une capacité",
  composer_role: "Composer un rôle",
  deleguer: "Déléguer",
};

export const LIBELLE_FORME: Record<FormePaiement, string> = {
  especes: "Espèces",
  mobile_money: "Mobile money",
  credit: "Crédit (créance)",
};

export const LIBELLE_STATUT_SERVICE: Record<StatutService, string> = {
  ouvert: "Ouvert",
  cloture: "Clôturé",
  scelle: "Scellé",
};

export const LIBELLE_STATUT_ADDITION: Record<StatutAddition, string> = {
  ouverte: "Ouverte",
  reglee: "Réglée",
  abandonnee: "Abandonnée",
};

export const TOUTES_CAPACITES: Capacite[] = [
  "ouvrir_service",
  "enregistrer_vente",
  "encaisser",
  "verser_recette",
  "cloturer_service",
  "creer_client",
  "accorder_credit",
  "encaisser_remboursement",
  "inscrire_produit",
  "tarifer",
  "retirer_produit",
  "creer_compte",
  "accorder_capacite",
  "retirer_capacite",
  "composer_role",
  "deleguer",
];
