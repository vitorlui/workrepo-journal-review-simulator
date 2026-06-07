"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV: { href: string; label: string }[] = [
  { href: "/", label: "Dashboard" },
  { href: "/reviews", label: "Reviews" },
  { href: "/reviews/new", label: "New Review" },
  { href: "/papers", label: "Papers" },
  { href: "/venues", label: "Venues" },
  { href: "/recent-papers", label: "Recent Papers / SOTA" },
  { href: "/external-prompts", label: "External Prompts" },
  { href: "/pending-requests", label: "Pending Requests" },
  { href: "/reviewer-profiles", label: "Reviewer Profiles" },
  { href: "/ai-engines", label: "AI Engines" },
  { href: "/settings", label: "Settings" },
  { href: "/export-history", label: "Export / History" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-64 shrink-0 border-r border-slate-200 bg-white min-h-screen">
      <div className="px-5 py-5 border-b border-slate-200">
        <div className="text-ieee-dark font-semibold leading-tight">Journal Review</div>
        <div className="text-ieee-dark font-semibold leading-tight">Simulator</div>
        <div className="text-xs text-slate-400 mt-1">pre-submission editorial sim</div>
      </div>
      <nav className="p-3 space-y-1">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-md px-3 py-2 text-sm ${
                active ? "bg-ieee text-white" : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
