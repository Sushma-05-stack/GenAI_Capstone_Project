"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ragApi, datasetsApi, feedbackApi } from "@/lib/api";
import { useToast } from "@/components/ui/toaster";
import { formatScore, scoreColor } from "@/lib/utils";
import { Send, ExternalLink, ThumbsUp, ThumbsDown, AlertTriangle } from "lucide-react";

export default function RAGQueryPage() {
  const { toast } = useToast();
  const [form, setForm] = useState({
    question: "",
    dataset_id: "",
    provider: "auto",
    top_k: 5,
  });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);

  const { data: datasetsData } = useQuery({
    queryKey: ["datasets-list"],
    queryFn: () => datasetsApi.list({ page_size: 100 }).then((r) => r.data),
  });

  const datasets = datasetsData?.datasets || [];

  const handleQuery = async () => {
    if (!form.question || !form.dataset_id) {
      toast({ title: "Fill in question and dataset", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const { data } = await ragApi.query(form);
      setResult(data);
      setHistory((prev) => [data, ...prev.slice(0, 9)]);
    } catch (err: any) {
      toast({
        title: "Query failed",
        description: err.response?.data?.detail || "Unknown error",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">RAG Query</h1>
        <p className="text-gray-500 text-sm">Test retrieval and generation in real-time</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Query Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl border p-5">
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Dataset</label>
                <select
                  value={form.dataset_id}
                  onChange={(e) => setForm({ ...form, dataset_id: e.target.value })}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select dataset</option>
                  {datasets.map((d: any) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Provider</label>
                <select
                  value={form.provider}
                  onChange={(e) => setForm({ ...form, provider: e.target.value })}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {["auto", "openai", "gemini", "groq", "claude"].map((p) => (
                    <option key={p} value={p}>{p === "auto" ? "Auto (Fallback)" : p}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="relative">
              <textarea
                value={form.question}
                onChange={(e) => setForm({ ...form, question: e.target.value })}
                onKeyDown={(e) => { if (e.key === "Enter" && e.ctrlKey) handleQuery(); }}
                className="w-full rounded-lg border px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none pr-12"
                rows={3}
                placeholder="Ask a question about your documents... (Ctrl+Enter to submit)"
              />
              <button
                onClick={handleQuery}
                disabled={loading}
                className="absolute right-3 bottom-3 p-2 bg-blue-600 rounded-lg text-white hover:bg-blue-700 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Result */}
          {loading && (
            <div className="bg-white rounded-xl border p-8 text-center">
              <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
              <p className="text-sm text-gray-500">Running RAG pipeline...</p>
            </div>
          )}

          {result && !loading && (
            <div className="bg-white rounded-xl border p-5 space-y-4">
              {/* Answer */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Answer</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                      {result.provider_used}/{result.model_used}
                    </span>
                    {result.fallback_used && (
                      <span className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" /> Fallback used
                      </span>
                    )}
                    <span className="text-xs text-gray-400">{result.latency_ms?.toFixed(0)}ms</span>
                  </div>
                </div>
                <p className="text-sm text-gray-800 leading-relaxed bg-blue-50 p-4 rounded-lg">
                  {result.answer}
                </p>
              </div>

              {/* LangSmith link */}
              {result.langsmith_trace_url && (
                <a href={result.langsmith_trace_url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                  <ExternalLink className="h-3 w-3" /> View in LangSmith
                </a>
              )}

              {/* Contexts */}
              {result.contexts?.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-2">
                    Retrieved Contexts ({result.contexts.length})
                  </span>
                  <div className="space-y-2">
                    {result.contexts.map((ctx: string, i: number) => (
                      <div key={i} className="text-xs bg-gray-50 p-3 rounded-lg border text-gray-700 leading-relaxed line-clamp-3">
                        <span className="font-medium text-gray-400">#{i + 1}: </span>{ctx}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* History sidebar */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-800 mb-3 text-sm">Query History</h3>
          {history.length === 0 ? (
            <p className="text-xs text-gray-400">No queries yet this session</p>
          ) : (
            <div className="space-y-2">
              {history.map((h: any, i: number) => (
                <button
                  key={i}
                  onClick={() => setResult(h)}
                  className="w-full text-left p-3 rounded-lg hover:bg-gray-50 border text-xs"
                >
                  <p className="font-medium text-gray-700 truncate">{h.question}</p>
                  <p className="text-gray-400 mt-0.5 truncate">{h.provider_used}/{h.model_used}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
