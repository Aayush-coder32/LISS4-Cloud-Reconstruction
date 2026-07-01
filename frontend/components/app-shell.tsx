"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import clsx from "clsx";
import { Activity, History, LayoutDashboard, LogOut } from "lucide-react";

import { clearToken } from "@/lib/api";
import { Button } from "@/components/ui/button";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/history", label: "History", icon: History },
  { href: "/login", label: "Access", icon: Activity }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(255,159,28,0.2),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(104,211,145,0.18),_transparent_30%),linear-gradient(160deg,#08131f,#0d3342_55%,#08131f)]">
      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6 lg:px-6">
        <aside className="hidden w-64 shrink-0 rounded-xl2 border border-white/10 bg-black/20 p-5 text-cloud shadow-panel backdrop-blur lg:block">
          <p className="font-mono text-xs uppercase tracking-[0.35em] text-mint/80">GenCloudNet</p>
          <h1 className="mt-3 text-2xl font-bold">Satellite Reconstruction Console</h1>
          <nav className="mt-8 space-y-2">
            {links.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-colors",
                  pathname === href ? "bg-white/12 text-white" : "text-cloud/70 hover:bg-white/5 hover:text-white"
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </nav>
          <Button
            variant="ghost"
            className="mt-8 w-full justify-start"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign out
          </Button>
        </aside>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
