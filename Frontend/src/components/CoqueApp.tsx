import { useEffect, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import {
  Beer,
  Coins,
  ClipboardList,
  Home,
  Users,
  Package,
  BookText,
  UserCog,
  ShieldCheck,
  Settings,
  LogOut,
  Activity,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getSante } from "@/api/endpoints";
import { deconnecter, useSession } from "@/etat/session";
import { cn } from "@/lib/utils";

const ROUTES_SANS_COQUE = new Set(["/connexion", "/bars", "/"]);

export function CoqueApp({ children }: { children: ReactNode }) {
  const loc = useLocation();
  const nav = useNavigate();
  const { jeton, barId } = useSession();

  useEffect(() => {
    if (typeof window === "undefined") return;
    const p = loc.pathname;
    if (!jeton && p !== "/connexion") {
      nav({ to: "/connexion" });
    } else if (jeton && !barId && p !== "/bars" && p !== "/connexion") {
      nav({ to: "/bars" });
    } else if (jeton && p === "/") {
      nav({ to: barId ? "/accueil" : "/bars" });
    }
  }, [loc.pathname, jeton, barId, nav]);

  const nu = ROUTES_SANS_COQUE.has(loc.pathname);
  if (nu) return <div className="min-h-screen bg-background">{children}</div>;

  return (
    <div className="min-h-screen bg-background pb-24">
      <BarreHaut />
      <main className="mx-auto max-w-2xl px-4 py-4">{children}</main>
      <BarreBas />
    </div>
  );
}

function BarreHaut() {
  const { data: sante } = useQuery({
    queryKey: ["sante"],
    queryFn: () => getSante().catch(() => null),
    refetchInterval: 30_000,
    retry: false,
  });
  const disponible = sante?.statut && !/panne|down|ko/i.test(sante.statut);
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur">
      <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
        <Link to="/accueil" className="flex items-center gap-2">
          <Beer className="h-5 w-5 text-primary" />
          <span className="font-semibold tracking-tight">SipTrack</span>
        </Link>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span
            className="flex items-center gap-1.5"
            title={sante ? `commit ${sante.commit} — base ${sante.base}` : "Service injoignable"}
          >
            <span
              className={cn(
                "inline-block h-2 w-2 rounded-full",
                disponible ? "bg-solde" : "bg-manquant",
              )}
            />
            {disponible ? "En ligne" : "Hors ligne"}
          </span>
          <button
            onClick={() => {
              deconnecter();
              window.location.assign("/connexion");
            }}
            className="inline-flex items-center gap-1 rounded px-2 py-1 hover:bg-muted"
          >
            <LogOut className="h-3.5 w-3.5" /> Quitter
          </button>
        </div>
      </div>
    </header>
  );
}

const ITEMS = [
  { to: "/accueil", label: "Service", icon: Home },
  { to: "/vente", label: "Vente", icon: Coins },
  { to: "/tables", label: "Tables", icon: ClipboardList },
  { to: "/creances", label: "Créances", icon: Users },
  { to: "/catalogue", label: "Catalogue", icon: BookText },
] as const;

const ITEMS_SECONDAIRES = [
  { to: "/inventaire", label: "Inventaire", icon: Package },
  { to: "/equipe", label: "Équipe", icon: UserCog },
  { to: "/journal-acces", label: "Consultations", icon: ShieldCheck },
  { to: "/reglages", label: "Réglages", icon: Settings },
] as const;

function BarreBas() {
  const loc = useLocation();
  return (
    <>
      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-card/95 backdrop-blur">
        <div className="mx-auto grid max-w-2xl grid-cols-5">
          {ITEMS.map(({ to, label, icon: Icon }) => {
            const actif = loc.pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex min-h-[64px] flex-col items-center justify-center gap-1 py-2 text-[11px]",
                  actif ? "text-primary" : "text-muted-foreground",
                )}
              >
                <Icon className="h-5 w-5" />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
      <div className="mx-auto mt-6 flex max-w-2xl flex-wrap justify-center gap-2 px-4">
        {ITEMS_SECONDAIRES.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Icon className="h-3.5 w-3.5" /> {label}
          </Link>
        ))}
        <Link
          to="/recette"
          className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
        >
          <Activity className="h-3.5 w-3.5" /> Verser recette
        </Link>
        <Link
          to="/cloture"
          className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
        >
          Clôture
        </Link>
      </div>
    </>
  );
}
