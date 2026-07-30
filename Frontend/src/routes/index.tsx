import { createFileRoute } from "@tanstack/react-router";

// Redirection gérée dans CoqueApp selon état de session.
export const Route = createFileRoute("/")({
  component: () => (
    <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
      Chargement…
    </div>
  ),
});
