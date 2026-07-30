import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TitrePage } from "@/components/ui-siptrack";
import { useSession, deconnecter, definirBar } from "@/etat/session";
import { ecrireServiceCourant, lireServiceCourant } from "@/etat/local";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ClipboardList } from "lucide-react";

export const Route = createFileRoute("/reglages")({
  head: () => ({
    meta: [
      { title: "Réglages — SipTrack" },
      { name: "description", content: "Réglages locaux : thème, service en repli." },
    ],
  }),
  component: PageReglages,
});

function PageReglages() {
  const { barId } = useSession();
  const [sid, setSid] = useState("");
  const [themeClair, setThemeClair] = useState(false);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const clair = localStorage.getItem("siptrack.theme") === "clair";
    setThemeClair(clair);
    document.documentElement.classList.toggle("light", clair);
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.classList.toggle("light", themeClair);
    localStorage.setItem("siptrack.theme", themeClair ? "clair" : "sombre");
  }, [themeClair]);

  const courant = barId ? lireServiceCourant(barId) : null;

  return (
    <div>
      <TitrePage titre="Réglages" />
      <div className="space-y-4">
        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 font-semibold">Thème</h2>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={themeClair} onChange={(e) => setThemeClair(e.target.checked)} />
            Thème clair (par défaut : sombre)
          </label>
        </section>

        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 font-semibold">Service en cours (repli)</h2>
          <p className="mb-2 text-xs text-muted-foreground">
            À utiliser si un service est déjà ouvert mais que cet appareil ne le connaît pas.
            Saisissez son identifiant.
          </p>
          <p className="mb-2 text-xs text-muted-foreground">Actuel : {courant ?? "aucun"}</p>
          <div className="flex gap-2">
            <Input
              icone={ClipboardList}
              value={sid}
              onChange={(e) => setSid(e.target.value)}
              placeholder="service_id"
            />
            <Button
              disabled={!sid.trim() || !barId}
              onClick={() => {
                ecrireServiceCourant(barId as string, sid.trim());
                setSid("");
                toast.success("Service enregistré localement.");
              }}
            >
              Enregistrer
            </Button>
          </div>
          {courant ? (
            <Button
              variant="ghost"
              className="mt-2"
              onClick={() => { ecrireServiceCourant(barId as string, null); toast.success("Service oublié localement."); }}
            >
              Oublier le service actuel
            </Button>
          ) : null}
        </section>

        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 font-semibold">Bar courant</h2>
          <p className="mb-2 text-xs text-muted-foreground">{barId ?? "aucun"}</p>
          <Button
            variant="outline"
            onClick={() => { definirBar(null); window.location.assign("/bars"); }}
          >
            Changer de bar
          </Button>
        </section>

        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-2 font-semibold">Session</h2>
          <Button variant="destructive" onClick={() => { deconnecter(); window.location.assign("/connexion"); }}>
            Se déconnecter
          </Button>
        </section>
      </div>
    </div>
  );
}
