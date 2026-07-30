// Types dérivés du contrat SipTrack, en français, sans invention.

export type FormePaiement = "especes" | "mobile_money" | "credit";
export type StatutService = "ouvert" | "cloture" | "scelle";
export type StatutAddition = "ouverte" | "reglee" | "abandonnee";

export type Capacite =
  | "ouvrir_service"
  | "enregistrer_vente"
  | "encaisser"
  | "verser_recette"
  | "cloturer_service"
  | "creer_client"
  | "accorder_credit"
  | "encaisser_remboursement"
  | "inscrire_produit"
  | "tarifer"
  | "retirer_produit"
  | "creer_compte"
  | "accorder_capacite"
  | "retirer_capacite"
  | "composer_role"
  | "deleguer";

export interface Bar {
  id: string;
  nom: string;
  proprietaire_id: string;
}

export interface Compte {
  id: string;
  bar_id: string;
  user_id: string;
  capacites: Capacite[];
}

export interface Produit {
  id: string;
  bar_id: string;
  nom: string;
  prix: number;
  en_vente: boolean;
}

export interface Service {
  id: string;
  bar_id: string;
  statut: StatutService;
  fond_de_caisse: number;
  ouvert_le: string;
  clos_le: string | null;
}

export interface Vente {
  id: string;
  service_id: string;
  produit_id: string;
  quantite: number;
  prix_unitaire: number;
  montant_total: number;
  forme_paiement: FormePaiement;
  addition_id: string | null;
}

export interface Addition {
  id: string;
  service_id: string;
  table_numero: number;
  statut: StatutAddition;
  ouvert_le: string;
  ferme_le: string | null;
}

export interface AdditionLigne {
  vente_id: string;
  produit_id: string;
  quantite: number;
  prix_unitaire: number;
  montant_total: number;
  forme_paiement: FormePaiement;
  horodatage: string;
}

export interface AdditionPaiementResume {
  paiement_id: string;
  montant: number;
  forme_paiement: FormePaiement;
  horodatage: string;
}

export interface AdditionDetail {
  id: string;
  service_id: string;
  table_numero: number;
  statut: StatutAddition;
  ouvert_le: string;
  ferme_le: string | null;
  lignes: AdditionLigne[];
  total: number;
  paiements: AdditionPaiementResume[];
  paye: number;
  reste_a_payer: number;
}

export interface Paiement {
  id: string;
  addition_id: string;
  service_id: string;
  montant: number;
  forme_paiement: FormePaiement;
  reste_a_payer: number;
}

export interface Versement {
  id: string;
  service_id: string;
  serveuse_id: string;
  attendu: number;
  verse: number;
  ecart: number;
}

export interface SousCaisse {
  serveuse_id: string;
  encaisse_especes: number;
  encaisse_mobile_money: number;
  verse: number | null;
  ecart: number | null;
}

export interface Client {
  id: string;
  bar_id: string;
  nom: string;
}

export interface Creance {
  credit_id: string;
  client_id: string;
  client_nom: string;
  service_id: string;
  addition_id: string;
  montant: number;
  rembourse: number;
  reste: number;
  statut: string;
}

export interface Encours {
  client_id: string;
  client_nom: string;
  total_du: number;
  total_rembourse: number;
  reste: number;
  creances: Creance[];
}

export interface ProduitStock {
  id: string;
  bar_id: string;
  nom: string;
  quantite: number;
}

export interface AccesEntree {
  administrateur_id: string;
  operation: string;
  horodatage: string;
}

export interface Sante {
  statut: string;
  commit: string;
  base: string;
}

export interface InscriptionEntree {
  username: string;
  password: string;
  email?: string;
  nom_bar: string;
}

export interface InscriptionSortie {
  user_id: string;
  bar_id: string;
  bar_nom: string;
  message: string;
}
