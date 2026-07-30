// Formatage XAF — entiers uniquement, espace insécable comme séparateur de milliers.
export function formatXAF(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  const entier = Math.trunc(n);
  const signe = entier < 0 ? "-" : "";
  const chiffres = Math.abs(entier).toString();
  const avecEspaces = chiffres.replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0");
  return `${signe}${avecEspaces}\u00A0FCFA`;
}

export function formatHeure(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}
export function formatDateHeure(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
