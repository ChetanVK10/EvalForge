import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { Moon, Search, Sun } from "lucide-react";
import { useState } from "react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const TITLES: { match: RegExp; title: string; crumbs: string[] }[] = [
  { match: /^\/$/, title: "Dashboard", crumbs: ["Overview"] },
  { match: /^\/datasets\/[^/]+$/, title: "Dataset Details", crumbs: ["Datasets", "Details"] },
  { match: /^\/datasets$/, title: "Datasets", crumbs: ["Datasets"] },
  { match: /^\/configurations/, title: "Configurations", crumbs: ["Configurations"] },
  { match: /^\/evaluations/, title: "New Evaluation", crumbs: ["Evaluations", "New run"] },
  {
    match: /^\/experiments\/[^/]+$/,
    title: "Experiment Results",
    crumbs: ["Experiments", "Results"],
  },
  { match: /^\/experiments$/, title: "Experiments", crumbs: ["Experiments"] },
  {
    match: /^\/regression/,
    title: "Regression Comparison",
    crumbs: ["Regression", "Baseline vs candidate"],
  },
  { match: /^\/settings/, title: "Settings", crumbs: ["Settings"] },
];

export function TopBar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const meta = TITLES.find((t) => t.match.test(pathname)) ?? {
    title: "LLMOps Studio",
    crumbs: [],
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur md:px-6">
      <div className="min-w-0">
        <h2 className="truncate text-sm font-semibold tracking-tight">{meta.title}</h2>
        <nav aria-label="Breadcrumb" className="num truncate text-[11px] text-muted-foreground">
          <Link to="/" className="hover:text-foreground">
            studio
          </Link>
          {meta.crumbs.map((c) => (
            <span key={c}> / {c.toLowerCase()}</span>
          ))}
        </nav>
      </div>

      <form
        className="ml-auto hidden w-64 items-center lg:flex"
        onSubmit={(e) => {
          e.preventDefault();
          navigate({ to: "/experiments", search: query ? { q: query } : {} });
        }}
      >
        <div className="relative w-full">
          <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search experiments…"
            className="h-8 pl-8 text-sm"
            aria-label="Search experiments"
          />
        </div>
      </form>

      <div className="ml-auto flex items-center gap-2 lg:ml-0">
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          onClick={toggleTheme}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
        <div className="flex items-center gap-2 border-l border-border pl-2">
          <span className="flex size-7 items-center justify-center rounded-sm bg-secondary text-[11px] font-semibold">
            AK
          </span>
          <div className="hidden leading-tight sm:block">
            <p className="text-xs font-medium">A. Keller</p>
            <p className="text-[10px] text-muted-foreground">AI Platform</p>
          </div>
        </div>
      </div>
    </header>
  );
}
