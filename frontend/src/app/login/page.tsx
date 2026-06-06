"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi, usersApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useToast } from "@/components/ui/toaster";
import { Eye, EyeOff, Zap } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { setTokens, setUser, logout } = useAuthStore();
  const { toast } = useToast();
  const [email, setEmail]       = useState("admin@rageval.com");
  const [password, setPassword] = useState("Admin123!");
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  // Clear any stale cached session on page load
  useEffect(() => {
    logout();
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("rag-eval-auth");
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.login({ email, password });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      setTokens(data.access_token, data.refresh_token);
      const { data: user } = await usersApi.getMe();
      setUser(user);
      router.push("/dashboard");
    } catch (err: any) {
      const detail = err.response?.data?.detail || "Invalid credentials. Use password: Admin123!";
      setError(detail);
      toast({ title: "Login failed", description: detail, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">

          {/* Logo */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl mb-3">
              <Zap className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">RAG Eval Dashboard</h1>
            <p className="text-gray-500 text-sm mt-1">Enterprise RAG Evaluation Platform</p>
          </div>

          {/* Credentials hint */}
          <div className="mb-5 bg-blue-50 border border-blue-200 rounded-xl p-4">
            <p className="text-xs font-semibold text-blue-700 mb-2">Available accounts:</p>
            <div className="space-y-1.5">
              {[
                { email: "admin@rageval.com",        role: "Admin",     desc: "Full access" },
                { email: "23eg107b20@anurag.edu.in", role: "Evaluator", desc: "Your account" },
              ].map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => { setEmail(acc.email); setPassword("Admin123!"); setError(""); }}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border text-xs transition-all ${
                    email === acc.email
                      ? "border-blue-500 bg-blue-100 text-blue-800"
                      : "border-gray-200 hover:border-blue-300 hover:bg-blue-50 text-gray-700"
                  }`}
                >
                  <span>
                    <span className="font-medium">{acc.email}</span>
                    <span className="text-gray-400 ml-2">({acc.desc})</span>
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    acc.role === "Admin" ? "bg-purple-100 text-purple-700" : "bg-green-100 text-green-700"
                  }`}>{acc.role}</span>
                </button>
              ))}
            </div>
            <p className="text-xs text-blue-600 mt-2 font-medium">
              Password for all accounts: <code className="bg-blue-100 px-1.5 py-0.5 rounded font-mono">Admin123!</code>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(""); }}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(""); }}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
                  autoComplete="current-password"
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2.5 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white rounded-lg py-2.5 font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  Signing in…
                </span>
              ) : "Sign In"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            New user?{" "}
            <Link href="/register" className="text-blue-600 hover:underline font-medium">Register</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
