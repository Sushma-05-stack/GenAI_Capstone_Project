"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

/**
 * Visit /reset-session to clear all cached tokens and force a fresh login.
 * Useful when a role change was made server-side.
 */
export default function ResetSessionPage() {
  const router = useRouter();
  const { logout } = useAuthStore();

  useEffect(() => {
    // Wipe everything
    logout();
    localStorage.clear();
    sessionStorage.clear();

    // Redirect to login after a brief pause
    setTimeout(() => {
      router.replace("/login");
    }, 1500);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white rounded-2xl shadow-xl p-8 text-center max-w-sm w-full">
        <div className="animate-spin h-10 w-10 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-gray-800">Clearing session...</h2>
        <p className="text-sm text-gray-500 mt-1">
          Resetting your session and redirecting to login.
        </p>
      </div>
    </div>
  );
}
