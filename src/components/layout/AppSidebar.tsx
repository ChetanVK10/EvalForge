import { Link, useRouterState } from "@tanstack/react-router";
import {
  Boxes,
  ChevronsLeft,
  ChevronsRight,
  Database,
  FlaskConical,
  GitCompareArrows,
  LayoutDashboard,
  Play,
  Settings as SettingsIcon,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard, exact: true },
  { label: "Datasets", to: "/datasets", icon: Database, exact: false },
  { label: "Configurations", to: "/configurations", icon: Boxes, exact: false },
  { label: "Evaluations", to: "/evaluations/new", icon: Play, exact: false },
  { label: "Experiments", to: "/experiments", icon: FlaskConical, exact: false },
  { label: "Regression", to: "/regression", icon: GitCompareArrows, exact: false },
  { label: "Settings", to: "/settings", icon: SettingsIcon, exact: false },
] as const;

export function AppSidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside
      className={cn(
        "sticky top-0 z-30 hidden h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 md:flex",
        collapsed ? "w-[60px]" : "w-[232px]",
      )}
    >
      <div
        className={cn(
          "flex h-14 items-center gap-2 border-b border-sidebar-border px-3",
          collapsed && "justify-center px-0",
        )}
      >
        <span className="flex size-7 shrink-0 items-center justify-center rounded-sm bg-primary text-primary-foreground">
          <Sparkles className="size-4" />
        </span>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight text-sidebar-foreground">
              LLMOps Studio
            </p>
            <p className="num truncate text-[10px] text-muted-foreground">eval · regression</p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
        {NAV.map((item) => {
          const active = item.exact
            ? pathname === item.to
            : pathname.startsWith(item.to.split("/").slice(0, 2).join("/"));
          return (
            <Link
              key={item.to}
              to={item.to}
              title={item.label}
              className={cn(
                "flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/75 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
                collapsed && "justify-center px-0",
              )}
            >
              <item.icon className="size-4 shrink-0" strokeWidth={2} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-sidebar-border p-2">
        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "flex w-full items-center gap-2.5 rounded-sm px-2.5 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
            collapsed && "justify-center px-0",
          )}
        >
          {collapsed ? (
            <ChevronsRight className="size-4" />
          ) : (
            <>
              <ChevronsLeft className="size-4" />
              Collapse
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
