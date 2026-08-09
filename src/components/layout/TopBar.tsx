import { useNavigate } from "@tanstack/react-router";
import { Moon, Search, Sun } from "lucide-react";
import { useState } from "react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function TopBar() {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-end gap-4 border-b border-border bg-background/95 px-4 backdrop-blur md:px-6">
      <form
        className="hidden w-64 items-center lg:flex"
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

      <Button
        variant="ghost"
        size="icon"
        className="size-8"
        onClick={toggleTheme}
        aria-label="Toggle theme"
      >
        {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
      </Button>
    </header>
  );
}
