// Mémoires locales pour combler les trous de l'API :
// - dernier service ouvert par bar
// - additions ouvertes créées depuis cet appareil, par service

export function lireServiceCourant(barId: string): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(`siptrack.service.${barId}`);
}
export function ecrireServiceCourant(barId: string, serviceId: string | null) {
  if (typeof localStorage === "undefined") return;
  const cle = `siptrack.service.${barId}`;
  if (serviceId) localStorage.setItem(cle, serviceId);
  else localStorage.removeItem(cle);
}

export interface AdditionLocale {
  id: string;
  table_numero: number;
}
export function lireAdditionsLocales(serviceId: string): AdditionLocale[] {
  if (typeof localStorage === "undefined") return [];
  const brut = localStorage.getItem(`siptrack.additions.${serviceId}`);
  if (!brut) return [];
  try {
    const v = JSON.parse(brut);
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}
export function ajouterAdditionLocale(serviceId: string, a: AdditionLocale) {
  const l = lireAdditionsLocales(serviceId);
  if (!l.some((x) => x.id === a.id)) {
    l.push(a);
    localStorage.setItem(`siptrack.additions.${serviceId}`, JSON.stringify(l));
  }
}
export function retirerAdditionLocale(serviceId: string, id: string) {
  const l = lireAdditionsLocales(serviceId).filter((x) => x.id !== id);
  localStorage.setItem(`siptrack.additions.${serviceId}`, JSON.stringify(l));
}
