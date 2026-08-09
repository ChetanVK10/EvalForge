import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";

import appCss from "../styles.css?url";

import { ThemeProvider } from "@/components/theme-provider";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { TopBar } from "@/components/layout/TopBar";
import { Toaster } from "@/components/ui/sonner";

function NotFoundComponent() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="num text-6xl font-semibold text-foreground">404</h1>
        <h2 className="mt-4 text-lg font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          This route does not exist in LLMOps Studio.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-sm bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Back to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    console.error("[LLMOps Studio] Root error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-lg font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The evaluation service returned an unexpected error.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-sm bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-sm border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
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
      { title: "LLMOps Studio" },
      {
        name: "description",
        content: "LLM evaluation, regression testing, and experiment management platform.",
      },
      { property: "og:title", content: "LLMOps Studio" },
      {
        property: "og:description",
        content: "LLM evaluation, regression testing, and experiment management platform.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon", sizes: "32x32" },
      { rel: "shortcut icon", href: "/favicon.ico" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
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

const MOBILE_NAV = [
  { label: "Dashboard", to: "/" },
  { label: "Datasets", to: "/datasets" },
  { label: "Configs", to: "/configurations" },
  { label: "New Eval", to: "/evaluations/new" },
  { label: "Experiments", to: "/experiments" },
  { label: "Regression", to: "/regression" },
  { label: "Settings", to: "/settings" },
] as const;

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <div className="flex min-h-screen w-full bg-background">
          <AppSidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar />
            <nav className="flex gap-1 overflow-x-auto border-b border-border px-3 py-2 md:hidden">
              {MOBILE_NAV.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className="rounded-sm px-2.5 py-1 text-xs font-medium whitespace-nowrap text-muted-foreground"
                  activeProps={{ className: "bg-accent text-accent-foreground" }}
                  activeOptions={{ exact: item.to === "/" }}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <main className="min-w-0 flex-1 px-4 py-5 md:px-6 md:py-6">
              {/* Required: nested routes render here. */}
              <Outlet />
            </main>
          </div>
        </div>
        <Toaster position="bottom-right" />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
