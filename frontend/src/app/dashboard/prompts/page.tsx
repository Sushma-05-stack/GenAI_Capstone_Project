"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { promptsApi, datasetsApi } from "@/lib/api";
import { useToast } from "@/components/ui/toaster";
import { Plus, GitCompare, BookOpen, X, Trash2, Loader2 } from "lucide-react";
import { formatScore, scoreColor } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Cell,
} from "recharts";

const DEFAULT_TEMPLATE = `You are a helpful AI assistant. Answer the question based ONLY on the provided context.
If the context does not contain enough information, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:`;

const STRICT_TEMPLATE = `You are a precise AI assistant. Use ONLY the information in the context below to answer.
Do NOT use any prior knowledge. If the answer is not in the context, respond with "Not found in documents."

Context:
{context}

Question: {question}

Strict Answer:`;

export default function PromptsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [newPrompt, setNewPrompt] = useState({
    name: "", version: "1.0", content: DEFAULT_TEMPLATE, description: "",
  });
  const [compareForm, setCompareForm] = useState({
    a: "", b: "", dataset_id: "", provider: "groq",
    model_name: "llama-3.3-70b-versatile", max_questions: "3",
  });
  const [compareResult, setCompareResult] = useState<any>(null);
  const [comparing, setComparing] = useState(false);

  const { data: prompts } = useQuery({
    queryKey: ["prompts"],
    queryFn: () => promptsApi.list().then((r) => r.data),
  });
  const { data: datasets } = useQuery({
    queryKey: ["datasets-list"],
    queryFn: () => datasetsApi.list({ page_size: 50 }).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => promptsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      toast({ title: "Prompt saved" });
      setShowCreate(false);
      setNewPrompt({ name: "", version: "1.0", content: DEFAULT_TEMPLATE, description: "" });
    },
    onError: (e: any) =>
      toast({ title: "Save failed", description: e.response?.data?.detail, variant: "destructive" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => promptsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      toast({ title: "Prompt deleted" });
    },
    onError: (e: any) =>
      toast({ title: "Delete failed", description: e.response?.data?.detail, variant: "destructive" }),
  });

  const handleDelete = (p: any) => {
    if (!confirm(`Delete prompt "${p.name} v${p.version}"?\n\nThis cannot be undone.`)) return;
    deleteMutation.mutate(p.id);
  };

  const handleCompare = async () => {
    if (!compareForm.a || !compareForm.b || !compareForm.dataset_id) {
      toast({ title: "Select Prompt A, Prompt B and a Dataset", variant: "destructive" });
      return;
    }
    if (compareForm.a === compareForm.b) {
      toast({ title: "Choose two different prompts", variant: "destructive" });
      return;
    }
    setComparing(true);
    setCompareResult(null);
    try {
      const { data } = await promptsApi.compare({
        prompt_a_id: compareForm.a,
        prompt_b_id: compareForm.b,
        dataset_id: compareForm.dataset_id,
        provider: compareForm.provider,
        model_name: compareForm.model_name,
        max_questions: parseInt(compareForm.max_questions),
      });
      setCompareResult(data);
    } catch (e: any) {
      toast({
        title: "Comparison failed",
        description: e.response?.data?.detail || "Unknown error",
        variant: "destructive",
      });
    } finally {
      setComparing(false);
    }
  };

  const promptList = Array.isArray(prompts) ? prompts : [];
  const datasetList = datasets?.datasets || [];

  // Build chart data from compare result
  const barData = compareResult
    ? [
        {
          metric: "Faithfulness",
          "Prompt A": +(compareResult.avg_faithfulness_a * 100).toFixed(1),
          "Prompt B": +(compareResult.avg_faithfulness_b * 100).toFixed(1),
        },
        {
          metric: "Relevancy",
          "Prompt A": +(compareResult.avg_relevancy_a * 100).toFixed(1),
          "Prompt B": +(compareResult.avg_relevancy_b * 100).toFixed(1),
        },
        {
          metric: "Hall. Risk",
          "Prompt A": +((1 - compareResult.avg_faithfulness_a) * 100).toFixed(1),
          "Prompt B": +((1 - compareResult.avg_faithfulness_b) * 100).toFixed(1),
        },
      ]
    : [];

  const radarData = compareResult
    ? [
        { metric: "Faithfulness",   A: +(compareResult.avg_faithfulness_a * 100).toFixed(1), B: +(compareResult.avg_faithfulness_b * 100).toFixed(1) },
        { metric: "Relevancy",      A: +(compareResult.avg_relevancy_a * 100).toFixed(1),    B: +(compareResult.avg_relevancy_b * 100).toFixed(1)    },
        { metric: "Low Hall. Risk", A: +((1 - compareResult.avg_faithfulness_a) < 0 ? 0 : ((1 - compareResult.avg_faithfulness_a) * 100)).toFixed(1) > 0 ? (100 - (1 - compareResult.avg_faithfulness_a) * 100).toFixed(1) : "0",
          B: (100 - (1 - compareResult.avg_faithfulness_b) * 100).toFixed(1) },
      ]
    : [];

  const winnerA = compareResult?.winner === "A";
  const winnerB = compareResult?.winner === "B";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prompt Library</h1>
          <p className="text-gray-500 text-sm">
            Version and A/B compare RAG prompt templates
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCompare(true)}
            className="flex items-center gap-2 px-4 py-2 border text-sm rounded-lg hover:bg-gray-50 font-medium"
          >
            <GitCompare className="h-4 w-4" /> A/B Compare
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 font-medium"
          >
            <Plus className="h-4 w-4" /> New Prompt
          </button>
        </div>
      </div>

      {/* Prompt cards */}
      {promptList.length === 0 ? (
        <div className="bg-white rounded-xl border p-12 text-center">
          <BookOpen className="h-10 w-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No prompts yet</p>
          <p className="text-gray-400 text-sm mt-1">
            Create a prompt template to compare performance across versions
          </p>
          <div className="flex gap-3 justify-center mt-4">
            <button
              onClick={() => {
                setNewPrompt({ name: "Default RAG Prompt", version: "1.0", content: DEFAULT_TEMPLATE, description: "Standard helpful assistant prompt" });
                setShowCreate(true);
              }}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
            >
              Add Default Template
            </button>
            <button
              onClick={() => {
                setNewPrompt({ name: "Strict Factual Prompt", version: "1.0", content: STRICT_TEMPLATE, description: "Strict no-hallucination prompt" });
                setShowCreate(true);
              }}
              className="px-4 py-2 border text-sm rounded-lg hover:bg-gray-50"
            >
              Add Strict Template
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {promptList.map((p: any) => (
            <div key={p.id} className="bg-white rounded-xl border p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-blue-500 flex-shrink-0" />
                  <span className="font-semibold text-gray-900">{p.name}</span>
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-500">
                    v{p.version}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      p.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {p.is_active ? "active" : "inactive"}
                  </span>
                  <button
                    onClick={() => handleDelete(p)}
                    disabled={deleteMutation.isPending && deleteMutation.variables === p.id}
                    title="Delete prompt"
                    className="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-40"
                  >
                    {deleteMutation.isPending && deleteMutation.variables === p.id
                      ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      : <Trash2 className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>
              {p.description && (
                <p className="text-xs text-gray-500 mb-3">{p.description}</p>
              )}
              <pre className="text-xs bg-gray-50 p-3 rounded-lg overflow-hidden whitespace-pre-wrap font-mono border text-gray-600 line-clamp-5">
                {p.content}
              </pre>
              {/* Metric badges */}
              {(p.avg_faithfulness != null || p.avg_answer_relevancy != null) && (
                <div className="flex gap-3 mt-3 pt-3 border-t">
                  {p.avg_faithfulness != null && (
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-gray-400">Faithful</span>
                      <span className={`font-semibold ${scoreColor(p.avg_faithfulness)}`}>
                        {formatScore(p.avg_faithfulness)}
                      </span>
                    </div>
                  )}
                  {p.avg_answer_relevancy != null && (
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-gray-400">Relevancy</span>
                      <span className={`font-semibold ${scoreColor(p.avg_answer_relevancy)}`}>
                        {formatScore(p.avg_answer_relevancy)}
                      </span>
                    </div>
                  )}
                  {p.avg_latency_ms != null && (
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-gray-400">Latency</span>
                      <span className="font-semibold text-gray-700">{p.avg_latency_ms.toFixed(0)}ms</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1 text-xs ml-auto">
                    <span className="text-gray-400">Eval runs</span>
                    <span className="font-semibold text-gray-700">{p.eval_count}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Create Modal ────────────────────────────────── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="font-bold text-lg">New Prompt Template</h2>
              <button onClick={() => setShowCreate(false)}>
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    value={newPrompt.name}
                    onChange={(e) => setNewPrompt({ ...newPrompt, name: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g. Strict Factual v2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
                  <input
                    value={newPrompt.version}
                    onChange={(e) => setNewPrompt({ ...newPrompt, version: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  value={newPrompt.description}
                  onChange={(e) => setNewPrompt({ ...newPrompt, description: e.target.value })}
                  className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="What makes this prompt special?"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template — use <code className="bg-gray-100 px-1 rounded">{"{context}"}</code> and{" "}
                  <code className="bg-gray-100 px-1 rounded">{"{question}"}</code>
                </label>
                <textarea
                  value={newPrompt.content}
                  onChange={(e) => setNewPrompt({ ...newPrompt, content: e.target.value })}
                  className="w-full rounded-lg border px-4 py-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={12}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">
                  Cancel
                </button>
                <button
                  onClick={() => createMutation.mutate(newPrompt)}
                  disabled={!newPrompt.name || createMutation.isPending}
                  className="px-6 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                  {createMutation.isPending ? "Saving..." : "Save Prompt"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Compare Modal ───────────────────────────────── */}
      {showCompare && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-auto">
          <div className="bg-white rounded-2xl w-full max-w-3xl shadow-2xl max-h-[95vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
              <div>
                <h2 className="font-bold text-lg">A/B Prompt Comparison</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Runs the same QA pairs through both prompts and compares RAGAS scores
                </p>
              </div>
              <button onClick={() => { setShowCompare(false); setCompareResult(null); }}>
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Selectors */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt A (baseline)
                  </label>
                  <select
                    value={compareForm.a}
                    onChange={(e) => setCompareForm({ ...compareForm, a: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Prompt A</option>
                    {promptList.map((p: any) => (
                      <option key={p.id} value={p.id}>{p.name} v{p.version}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt B (challenger)
                  </label>
                  <select
                    value={compareForm.b}
                    onChange={(e) => setCompareForm({ ...compareForm, b: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Prompt B</option>
                    {promptList.map((p: any) => (
                      <option key={p.id} value={p.id}>{p.name} v{p.version}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dataset</label>
                  <select
                    value={compareForm.dataset_id}
                    onChange={(e) => setCompareForm({ ...compareForm, dataset_id: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select dataset</option>
                    {datasetList.map((d: any) => (
                      <option key={d.id} value={d.id}>{d.name} ({d.qa_count} QAs)</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                  <select
                    value={compareForm.provider}
                    onChange={(e) => setCompareForm({ ...compareForm, provider: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {["groq", "openai", "gemini", "claude"].map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Questions</label>
                  <input
                    type="number" min="1" max="20"
                    value={compareForm.max_questions}
                    onChange={(e) => setCompareForm({ ...compareForm, max_questions: e.target.value })}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleCompare}
                  disabled={comparing || !compareForm.a || !compareForm.b || !compareForm.dataset_id}
                  className="px-6 py-2.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                  {comparing ? (
                    <span className="flex items-center gap-2">
                      <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                      Running comparison…
                    </span>
                  ) : "Run A/B Comparison"}
                </button>
              </div>

              {/* ── Results ─────────────────────────────── */}
              {compareResult && (
                <div className="space-y-5 pt-2 border-t">
                  {/* Winner banner */}
                  <div className={`rounded-xl p-4 text-center ${
                    compareResult.winner === "A" ? "bg-blue-50 border border-blue-200"
                    : compareResult.winner === "B" ? "bg-green-50 border border-green-200"
                    : "bg-gray-50 border border-gray-200"
                  }`}>
                    <p className="text-xs font-medium text-gray-500 mb-1">WINNER</p>
                    <p className={`text-3xl font-bold ${
                      compareResult.winner === "A" ? "text-blue-700"
                      : compareResult.winner === "B" ? "text-green-700"
                      : "text-gray-600"
                    }`}>
                      {compareResult.winner === "tie" ? "It's a Tie" : `Prompt ${compareResult.winner}`}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Based on {compareResult.questions_evaluated} question(s) ·{" "}
                      {compareResult.winner !== "tie"
                        ? `better faithfulness & relevancy`
                        : "scores are equal"}
                    </p>
                  </div>

                  {/* Score table */}
                  <div className="grid grid-cols-3 gap-3 text-center text-sm">
                    {[
                      { label: "Faithfulness A", value: compareResult.avg_faithfulness_a, color: "text-blue-700" },
                      { label: "Faithfulness B", value: compareResult.avg_faithfulness_b, color: "text-green-700" },
                      { label: "Δ Faithfulness", value: compareResult.faithfulness_diff, isDiff: true },
                      { label: "Relevancy A", value: compareResult.avg_relevancy_a, color: "text-blue-700" },
                      { label: "Relevancy B", value: compareResult.avg_relevancy_b, color: "text-green-700" },
                      { label: "Δ Relevancy", value: compareResult.relevancy_diff, isDiff: true },
                      { label: "Latency Δ", value: compareResult.latency_diff_ms, isMs: true, isDiff: true },
                      { label: "Cost Δ (USD)", value: compareResult.cost_diff_usd, isUsd: true, isDiff: true },
                    ].map((m, i) => (
                      <div key={i} className="bg-gray-50 rounded-lg p-3 border">
                        <p className="text-xs text-gray-500 mb-1">{m.label}</p>
                        <p className={`text-lg font-bold ${
                          m.isDiff
                            ? m.value > 0 ? "text-green-600" : m.value < 0 ? "text-red-600" : "text-gray-500"
                            : m.color || "text-gray-800"
                        }`}>
                          {m.isMs
                            ? `${m.value > 0 ? "+" : ""}${m.value?.toFixed(0)}ms`
                            : m.isUsd
                            ? `${m.value > 0 ? "+" : ""}$${m.value?.toFixed(5)}`
                            : m.isDiff
                            ? `${m.value > 0 ? "+" : ""}${(m.value * 100)?.toFixed(1)}%`
                            : formatScore(m.value)}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Bar chart */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">
                      Side-by-Side Metric Comparison
                    </h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={barData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                        <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10 }} />
                        <Tooltip formatter={(v: number) => `${v?.toFixed(1)}%`} />
                        <Legend />
                        <Bar dataKey="Prompt A" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="Prompt B" fill="#10B981" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Radar chart */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">
                      Radar Comparison (Prompt A vs B)
                    </h3>
                    <ResponsiveContainer width="100%" height={230}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#E5E7EB" />
                        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} tickCount={3} />
                        <Radar name="Prompt A" dataKey="A" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.2} />
                        <Radar name="Prompt B" dataKey="B" stroke="#10B981" fill="#10B981" fillOpacity={0.2} />
                        <Legend />
                        <Tooltip formatter={(v: number) => `${Number(v)?.toFixed(1)}%`} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
