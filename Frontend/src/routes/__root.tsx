import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import { Toaster } from "@/components/ui/sonner";
import { CoqueApp } from "@/components/CoqueApp";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-6xl font-bold">404</h1>
        <p className="mt-2 text-sm text-muted-foreground">Cet écran n'existe pas.</p>
        <a
          href="/"
          className="mt-6 inline-block rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
        >
          Revenir à l'accueil
        </a>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold">Un incident empêche cet écran de s'afficher.</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <div className="mt-6 flex justify-center gap-2">
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            onClick={() => {
              router.invalidate();
              reset();
            }}
          >
            Réessayer
          </button>
          <a href="/" className="rounded-md border border-input px-4 py-2 text-sm">
            Accueil
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "SipTrack — Le registre du bar" },
      {
        name: "description",
        content:
          "SipTrack : le registre incontestable des ventes, encaissements et sous-caisses de votre bar.",
      },
      { name: "author", content: "SipTrack" },
      { property: "og:title", content: "SipTrack — Le registre du bar" },
      {
        property: "og:description",
        content:
          "SipTrack : le registre incontestable des ventes, encaissements et sous-caisses de votre bar.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "twitter:title", content: "SipTrack — Le registre du bar" },
      {
        name: "twitter:description",
        content:
          "SipTrack : le registre incontestable des ventes, encaissements et sous-caisses de votre bar.",
      },
      {
        property: "og:image",
        content:
          "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/119bdd77-b6e3-40e3-bf8a-ed8cd81cce99/id-preview-512a1666--e88127b2-0b54-4e58-8aee-f9a0f7ca88f8.lovable.app-1785339608364.png",
      },
      {
        name: "twitter:image",
        content:
          "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/119bdd77-b6e3-40e3-bf8a-ed8cd81cce99/id-preview-512a1666--e88127b2-0b54-4e58-8aee-f9a0f7ca88f8.lovable.app-1785339608364.png",
      },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <CoqueApp>
        <Outlet />
      </CoqueApp>
      <Toaster richColors position="top-center" />
    </QueryClientProvider>
  );
}
