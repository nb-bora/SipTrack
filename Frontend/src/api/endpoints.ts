// Wrappers typés sur les endpoints. Aucun nom inventé : voir le contrat §3.
import { BASE, ecrire, lire } from "./client";
import type {
  AccesEntree,
  Addition,
  AdditionDetail,
  Bar,
  Client,
  Compte,
  Encours,
  FormePaiement,
  InscriptionEntree,
  InscriptionSortie,
  Paiement,
  Produit,
  ProduitStock,
  Sante,
  Service,
  SousCaisse,
  Vente,
  Versement,
  Capacite,
} from "./types";

// Auth (publique)
export const authJeton = (username: string, password: string) =>
  fetch(`${BASE}/api/auth/jeton/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ username, password }),
  });

export const inscrire = (username: string, password: string, nom_bar: string, email?: string) =>
  fetch(`${BASE}/api/inscription/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ username, password, email: email || "", nom_bar }),
  });

export const deconnecter = (cle?: string) =>
  ecrire<void>("POST", "/api/auth/deconnexion/", undefined, { cle });

export const getSante = () => lire<Sante>("/api/sante/", { auth: false });

// Bars & comptes
export const listerBars = () => lire<Bar[]>("/api/bars/");
export const creerBar = (nom: string, cle?: string) => ecrire<Bar>("POST", "/api/bars/", { nom }, { cle });

export const creerCompte = (bar_id: string, user_id: string, capacites_initiales: Capacite[], cle?: string) =>
  ecrire<Compte>("POST", "/api/comptes/", { bar_id, user_id, capacites_initiales }, { cle });
export const ajouterCapacite = (compteId: string, capacite: Capacite, cle?: string) =>
  ecrire<Compte>("POST", `/api/comptes/${compteId}/capacites/`, { capacite }, { cle });
export const retirerCapacite = (compteId: string, capacite: Capacite, cle?: string) =>
  ecrire<Compte>("DELETE", `/api/comptes/${compteId}/capacites/`, { capacite }, { cle });

export const listerAcces = (barId: string) => lire<AccesEntree[]>(`/api/bars/${barId}/acces/`);

// Catalogue
export const listerProduits = (barId: string) => lire<Produit[]>(`/api/bars/${barId}/produits/`);
export const creerProduit = (bar_id: string, nom: string, prix: number, cle?: string) =>
  ecrire<Produit>("POST", "/api/produits/", { bar_id, nom, prix }, { cle });
export const tariferProduit = (id: string, prix: number, cle?: string) =>
  ecrire<Produit>("POST", `/api/produits/${id}/tarif/`, { prix }, { cle });
export const retirerProduit = (id: string, cle?: string) =>
  ecrire<Produit>("POST", `/api/produits/${id}/retrait/`, undefined, { cle });

// Service & ventes
export const ouvrirService = (bar_id: string, fond_de_caisse: number, cle?: string) =>
  ecrire<Service>("POST", "/api/services/", { bar_id, fond_de_caisse }, { cle });
export const getService = (id: string) => lire<Service>(`/api/services/${id}/`);
export const cloturerService = (id: string, cle?: string) =>
  ecrire<Service>("POST", `/api/services/${id}/cloture/`, undefined, { cle });

export const enregistrerVente = (
  serviceId: string,
  payload: { produit_id: string; quantite: number; forme_paiement: FormePaiement; addition_id?: string },
  cle?: string,
) => ecrire<Vente>("POST", `/api/services/${serviceId}/ventes/`, payload, { cle });

export const ouvrirAddition = (serviceId: string, table_numero: number, cle?: string) =>
  ecrire<Addition>("POST", `/api/services/${serviceId}/additions/`, { table_numero }, { cle });
export const getAddition = (serviceId: string, additionId: string) =>
  lire<AdditionDetail>(`/api/services/${serviceId}/additions/${additionId}/`);
export const encaisserPaiement = (
  serviceId: string,
  additionId: string,
  payload: { montant: number; forme_paiement: FormePaiement; client_id?: string },
  cle?: string,
) =>
  ecrire<Paiement>("POST", `/api/services/${serviceId}/additions/${additionId}/paiements/`, payload, { cle });
export const reglerAddition = (serviceId: string, additionId: string, cle?: string) =>
  ecrire<Addition>("POST", `/api/services/${serviceId}/additions/${additionId}/reglement/`, undefined, { cle });

export const verserRecette = (serviceId: string, montant: number, cle?: string) =>
  ecrire<Versement>("POST", `/api/services/${serviceId}/versement/`, { montant }, { cle });
export const listerSousCaisses = (serviceId: string) =>
  lire<SousCaisse[]>(`/api/services/${serviceId}/sous-caisses/`);

// Clients & créances
export const creerClient = (bar_id: string, nom: string, cle?: string) =>
  ecrire<Client>("POST", "/api/clients/", { bar_id, nom }, { cle });
export const getEncoursClient = (clientId: string) => lire<Encours>(`/api/clients/${clientId}/encours/`);
export const listerEncoursBar = (barId: string) => lire<Encours[]>(`/api/bars/${barId}/encours/`);
export const rembourserCredit = (creditId: string, montant: number, cle?: string) =>
  ecrire("POST", `/api/credits/${creditId}/remboursements/`, { montant }, { cle });

// Inventaire
export const listerStock = (barId: string) =>
  lire<ProduitStock[]>(`/api/inventaire/produits/?bar_id=${encodeURIComponent(barId)}`);
export const inscrireStock = (bar_id: string, nom: string, quantite_initiale: number, cle?: string) =>
  ecrire<ProduitStock>("POST", "/api/inventaire/produits/", { bar_id, nom, quantite_initiale }, { cle });
export const ajusterStock = (id: string, quantite: number, cle?: string) =>
  ecrire<ProduitStock>("POST", `/api/inventaire/produits/${id}/stock/`, { quantite }, { cle });
export const vendreStock = (id: string, quantite: number, cle?: string) =>
  ecrire<ProduitStock>("POST", `/api/inventaire/produits/${id}/vendre/`, { quantite }, { cle });
export const corrigerInventaire = (id: string, quantite_nouvelle: number, raison: string, cle?: string) =>
  ecrire<ProduitStock>(
    "PUT",
    `/api/inventaire/produits/${id}/inventaire/`,
    { quantite_nouvelle, raison },
    { cle },
  );
