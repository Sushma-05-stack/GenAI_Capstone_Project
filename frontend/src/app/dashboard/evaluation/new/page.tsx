"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { evaluationApi, datasetsApi, promptsApi } from "@/lib/api";
import { useToast } from "@/components/ui/toaster";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { RoleErrorBanner } from "@/components/ui/role-error-banner";

const PROVIDERS = [
  { value: "auto", label: "Auto (Fallback Chain)" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Gemini" },
  { value: "groq", label: "Groq" },
  { value: "claude", label: "Claude" },
];

const MODELS_BY_PROVIDER: Record<string, string[]> = {
  auto: [],
  openai: ["gpt-4o", "gpt-4o-mini"],
  gemini: ["gemini-1.5-pro", "gemini-1.5-flash"],
  groq: ["llama3-70b-8192", "llama3-8b-8192"],
  claude: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
};

export default function NewEvaluationPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [form, setForm] = useState({
    name: "",
    dataset_id: "",
    provider: "auto",
    model_name: "",
    prompt_version_id: "",
    max_questions: "",
  });
  const [loading, setLoading] = useState(false);

  const { data: datasetsData } = useQuery({
    queryKey: ["datasets-list"],
    queryFn: () => datasetsApi.list({ page_size: 100 }).then((r) => r.data),
  });

  const { data: promptsData } = useQuery({
    queryKey: ["prompts-list"],
    queryFn: () => promptsApi.list().then((r) => r.data),
  });

  const datasets = datasetsData?.datasets || [];
  const prompts = promptsData || [];
  const models = MODELS_BY_PROVIDER[form.provider] || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.dataset_id) {
      toast({ title: "Select a dataset", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const payload = {
        name: form.name,
        dataset_id: form.dataset_id,
        provider: form.provider,
        model_name: form.model_name || (models[0] || "gpt-4o"),
        prompt_version_id: form.prompt_version_id || undefined,
        max_questions: form.max_questions ? parseInt(form.max_questions) : undefined,
      };
      await evaluationApi.startRun(payload);
      toast({ title: "Evaluation started", description: "Processing in the background" });
      router.push("/dashboard/evaluation");
    } catch (err: any) {
      toast({
        title: "Failed to start evaluation",
        description: err.response?.data?.detail || "Unknown error",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/evaluation" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">New Evaluation Run</h1>
          <p className="text-gray-500 text-sm">Configure and start a RAGAS evaluation</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Run Name *</label>
          <input
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., GPT-4o vs Gemini Eval v1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Dataset *</label>
          <select
            required
            value={form.dataset_id}
            onChange={(e) => setForm({ ...form, dataset_id: e.target.value })}
            className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a dataset</option>
            {datasets.map((d: any) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.qa_count} QA pairs)
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">LLM Provider</label>
            <select
              value={form.provider}
              onChange={(e) => setForm({ ...form, provider: e.target.value, model_name: "" })}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              value={form.model_name}
              onChange={(e) => setForm({ ...form, model_name: e.target.value })}
              disabled={form.provider === "auto"}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            >
              <option value="">{form.provider === "auto" ? "Auto-selected" : "Select model"}</option>
              {models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Prompt Version (optional)</label>
            <select
              value={form.prompt_version_id}
              onChange={(e) => setForm({ ...form, prompt_version_id: e.target.value })}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Default prompt</option>
              {prompts.map((p: any) => (
                <option key={p.id} value={p.id}>
                  {p.name} v{p.version}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Questions (optional)</label>
            <input
              type="number"
              value={form.max_questions}
              onChange={(e) => setForm({ ...form, max_questions: e.target.value })}
              className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="All questions"
              min="1"
            />
          </div>
        </div>

        <div className="pt-2 border-t flex justify-end gap-3">
          <Link
            href="/dashboard/evaluation"
            className="px-4 py-2.5 text-sm border rounded-lg hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Starting..." : "Start Evaluation"}
          </button>
        </div>
      </form>
    </div>
  );
}
