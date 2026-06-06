"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import {
  LayoutDashboard,
  Database,
  FlaskConical,
  MessageSquare,
  Zap,
  BarChart2,
  Shield,
  Settings,
  LogOut,
  BookOpen,
  GitCompare,
  AlertTriangle,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/datasets", label: "Datasets", icon: Database },
  { href: "/dashboard/evaluation", label: "Evaluations", icon: FlaskConical },
  { href: "/dashboard/prompts", label: "Prompts", icon: BookOpen },
  { href: "/dashboard/models", label: "Model Benchmark", icon: GitCompare },
  { href: "/dashboard/query", label: "RAG Query", icon: MessageSquare },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart2 },
  {
    href: "/dashboard/security",
    label: "Security Logs",
    icon: Shield,
    adminOnly: true,
  },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("rag-eval-auth");
    router.push("/login");
  };

  return (
    <aside className="w-64 min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-sm">RAG Eval</p>
            <p className="text-xs text-gray-400">Dashboard</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          if (item.adminOnly && user?.role !== "admin") return null;
          const Icon = item.icon;
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Stale-session warning */}
      {user?.role === "viewer" && (
        <div className="mx-3 mb-3 p-3 bg-amber-900/50 border border-amber-700 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-amber-300">Session outdated</p>
              <p className="text-xs text-amber-400 mt-0.5">
                Your role was upgraded. Re-login to apply.
              </p>
              <Link
                href="/reset-session"
                className="mt-1.5 block text-xs bg-amber-600 hover:bg-amber-500 text-white px-2 py-1 rounded text-center"
              >
                Re-login now
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* User */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium truncate">
              {user?.full_name || user?.username}
            </p>
            <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-xs text-gray-400 hover:text-red-400 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
