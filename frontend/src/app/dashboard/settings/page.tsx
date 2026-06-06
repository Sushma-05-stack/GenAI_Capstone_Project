"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { usersApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useToast } from "@/components/ui/toaster";
import { User, Key, Bell } from "lucide-react";

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const { toast } = useToast();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
  });

  const mutation = useMutation({
    mutationFn: (data: any) => usersApi.updateMe(data),
    onSuccess: ({ data }) => {
      setUser(data);
      toast({ title: "Profile updated" });
    },
    onError: () =>
      toast({
        title: "Update failed",
        variant: "destructive",
      }),
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm">Manage your profile and preferences</p>
      </div>

      {/* Profile */}
      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-5">
          <User className="h-5 w-5 text-blue-500" />
          <h2 className="font-semibold text-gray-800">Profile</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              disabled
              value={user?.email || ""}
              className="w-full rounded-lg border px-4 py-2.5 text-sm bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              disabled
              value={user?.username || ""}
              className="w-full rounded-lg border px-4 py-2.5 text-sm bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <span className="inline-flex items-center px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 text-sm font-medium capitalize">
              {user?.role}
            </span>
          </div>
          <div className="pt-2">
            <button
              onClick={() => mutation.mutate(form)}
              disabled={mutation.isPending}
              className="px-5 py-2.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {mutation.isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </div>

      {/* API Keys info */}
      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Key className="h-5 w-5 text-blue-500" />
          <h2 className="font-semibold text-gray-800">LLM Providers</h2>
        </div>
        <div className="space-y-3">
          {[
            { name: "OpenAI (GPT-4o)", env: "OPENAI_API_KEY", status: "configured" },
            { name: "Groq (Llama3 70B)", env: "GROQ_API_KEY", status: "configured" },
            { name: "Google Gemini", env: "GOOGLE_API_KEY", status: "check .env" },
            { name: "Anthropic Claude", env: "ANTHROPIC_API_KEY", status: "optional" },
          ].map((p) => (
            <div key={p.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-800">{p.name}</p>
                <p className="text-xs text-gray-400 font-mono">{p.env}</p>
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  p.status === "configured"
                    ? "bg-green-100 text-green-700"
                    : p.status === "optional"
                    ? "bg-gray-100 text-gray-500"
                    : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {p.status}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-3">
          API keys are configured in <code className="font-mono bg-gray-100 px-1 py-0.5 rounded">backend/.env</code>
        </p>
      </div>

      {/* About */}
      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="h-5 w-5 text-blue-500" />
          <h2 className="font-semibold text-gray-800">About</h2>
        </div>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Backend</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">FastAPI 0.111</span>
          </div>
          <div className="flex justify-between">
            <span>Frontend</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">Next.js 14</span>
          </div>
          <div className="flex justify-between">
            <span>Evaluation</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">RAGAS 0.1.21</span>
          </div>
          <div className="flex justify-between">
            <span>Vector DB</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">ChromaDB 0.5</span>
          </div>
          <div className="flex justify-between">
            <span>Database</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">MongoDB Atlas</span>
          </div>
        </div>
      </div>
    </div>
  );
}
