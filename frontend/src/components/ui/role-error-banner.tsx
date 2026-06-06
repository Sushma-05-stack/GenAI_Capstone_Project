"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { AlertTriangle } from "lucide-react";

interface Props {
  error: any;
}

export function RoleErrorBanner({ error }: Props) {
  const router = useRouter();
  const { logout } = useAuthStore();
  const detail = error?.response?.data?.detail || "";
  const isRoleError =
    typeof detail === "string" && detail.toLowerCase().includes("role");

  if (!isRoleError) return null;

  const handleReLogin = () => {
    logout();
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("rag-eval-auth");
    router.push("/login");
  };

  return (
    <div className="mb-4 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
      <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm font-medium text-amber-800">
          Permission changed — your session is outdated
        </p>
        <p className="text-xs text-amber-600 mt-0.5">
          Your account role was recently updated. Please sign in again to apply
          the new permissions.
        </p>
      </div>
      <button
        onClick={handleReLogin}
        className="flex-shrink-0 text-xs bg-amber-600 text-white px-3 py-1.5 rounded-lg hover:bg-amber-700"
      >
        Re-login
      </button>
    </div>
  );
}
