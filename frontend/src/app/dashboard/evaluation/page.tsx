"use client";

import { useState, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { evaluationApi, reportsApi } from "@/lib/api";
import { formatScore, scoreColor, downloadBlob } from "@/lib/utils";
import { useToast } from "@/components/ui/toaster";
import {
  Plus, Download, ExternalLink, RefreshCw,
  CheckCircle, Clock, XCircle, Loader2, Trash2,
} from "lucide-react";
import { format } from "date-fns";

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pending:   { label: "Pending",   color: "bg-gray-100 text-gray-600",   icon: <Clock className="h-3 w-3" /> },
  running:   { label: "Running",   color: "bg-blue-100 text-blue-700",   icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  completed: { label: "Completed", color: "bg-green-100 text-green-700", icon: <CheckCircle className="h-3 w-3" /> },
  failed:    { label: "Failed",    color: "bg-red-100 text-red-700",     icon: <XCircle className="h-3 w-3" /> },
};

export default function EvaluationPage() {
  const [page, setPage] = useState(1);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data, isLoading } = useQuery({
    queryKey: ["evaluation-history", page],
    queryFn: () => evaluationApi.getHistory({ page, page_size: 20 }).then((r) => r.data),
    refetchInterval: (query) => {
      const runs = query.state.data?.runs ?? [];
      const hasActive = runs.some((r: any) => r.status === "running" || r.status === "pending");
      return hasActive ? 4000 : false;
    },
  });

  const invalidateAll = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ["evaluation-history"] });
    await queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    await queryClient.invalidateQueries({ queryKey: ["trends"] });
    await queryClient.invalidateQueries({ queryKey: ["eval-history-analytics"] });
  }, [queryClient]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await invalidateAll();
    setIsRefreshing(false);
  }, [invalidateAll]);

  const handleDelete = useCallback(async (runId: string, runName: string) => {
    if (!confirm(`Delete "${runName}"?\n\nThis will permanently remove all per-question results. Cannot be undone.`)) return;
    setDeletingId(runId);
    try {
      await evaluationApi.deleteRun(runId);
      toast({ title: "Evaluation deleted", description: `"${runName}" removed` });
      await invalidateAll();
    } catch (e: any) {
      toast({
        title: "Delete failed",
        description: e.response?.data?.detail || "Unknown error",
        variant: "destructive",
      });
    } finally {
      setDeletingId(null);
    }
  }, [invalidateAll, toast]);

  const handleExport = async (runId: string, fmt: "csv" | "excel" | "pdf") => {
    try {
      const fnMap = {
        csv:   [reportsApi.exportCsv,   `eval_${runId}.csv`],
        excel: [reportsApi.exportExcel, `eval_${runId}.xlsx`],
        pdf:   [reportsApi.exportPdf,   `eval_${runId}.pdf`],
      } as const;
      const [fn, filename] = fnMap[fmt];
      const res = await (fn as any)(runId);
      downloadBlob(res.data, filename);
    } catch (e: any) {
      toast({ title: "Export failed", description: e.message, variant: "destructive" });
    }
  };

  const runs = data?.runs || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / 20);
  const hasRunning = runs.some((r: any) => r.status === "running" || r.status === "pending");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evaluations</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            RAGAS evaluation runs — {total} total
            {hasRunning && (
              <span className="ml-2 inline-flex items-center gap-1 text-blue-600 text-xs font-medium">
                <Loader2 className="h-3 w-3 animate-spin" />
                auto-refreshing
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 transition-colors font-medium"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            {isRefreshing ? "Refreshing…" : "Refresh"}
          </button>
          <Link
            href="/dashboard/evaluation/new"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 font-medium"
          >
            <Plus className="h-4 w-4" /> New Evaluation
          </Link>
        </div>
      </div>

      {/* Active run banner */}
      {hasRunning && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl px-5 py-3 flex items-center gap-3">
          <Loader2 className="h-5 w-5 text-blue-600 animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800">Evaluation in progress</p>
            <p className="text-xs text-blue-600">Auto-updates every 4 seconds. Click Refresh to update manually.</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && runs.length === 0 && (
        <div className="bg-white rounded-xl border p-16 text-center">
          <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-8 w-8 text-blue-400" />
          </div>
          <p className="text-gray-600 font-medium mb-1">No evaluation runs yet</p>
          <p className="text-gray-400 text-sm mb-5">Create a dataset with QA pairs, then run an evaluation</p>
          <Link href="/dashboard/evaluation/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 font-medium">
            <Plus className="h-4 w-4" /> Start First Evaluation
          </Link>
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="bg-white rounded-xl border overflow-hidden">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-4 border-b animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-32" />
              <div className="h-4 bg-gray-200 rounded w-20" />
              <div className="h-4 bg-gray-200 rounded w-16" />
              <div className="h-4 bg-gray-200 rounded w-16" />
              <div className="h-4 bg-gray-200 rounded w-16 ml-auto" />
            </div>
          ))}
        </div>
      )}

      {/* Runs table */}
      {!isLoading && runs.length > 0 && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {["Name", "Model", "Status", "Faithfulness", "Relevancy", "Hall. Risk",
                  "Latency", "Cost", "Date", "Actions"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {runs.map((run: any) => {
                const statusCfg = STATUS_CONFIG[run.status] ?? STATUS_CONFIG.pending;
                const isRunning = run.status === "running" || run.status === "pending";
                const isDeleting = deletingId === run.id;

                return (
                  <tr key={run.id}
                    className={`transition-colors ${isDeleting ? "opacity-40" : isRunning ? "bg-blue-50/40" : "hover:bg-gray-50"}`}>

                    <td className="px-4 py-3 font-medium text-gray-900 max-w-[160px]">
                      <span className="truncate block">{run.name}</span>
                    </td>

                    <td className="px-4 py-3">
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">{run.provider}</span>
                      <span className="text-xs text-gray-400 ml-1">{run.model_name}</span>
                    </td>

                    <td className="px-4 py-3 min-w-[120px]">
                      <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${statusCfg.color}`}>
                        {statusCfg.icon}
                        {statusCfg.label}
                        {isRunning && run.total_questions > 0 && (
                          <span className="opacity-70">{run.completed_questions}/{run.total_questions}</span>
                        )}
                      </span>
                      {isRunning && run.total_questions > 0 && (
                        <div className="mt-1.5 w-full bg-blue-100 rounded-full h-1.5">
                          <div className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                            style={{ width: `${(run.completed_questions / run.total_questions) * 100}%` }} />
                        </div>
                      )}
                    </td>

                    <td className={`px-4 py-3 font-medium ${scoreColor(run.avg_faithfulness)}`}>
                      {run.status === "completed" ? formatScore(run.avg_faithfulness) : "—"}
                    </td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(run.avg_answer_relevancy)}`}>
                      {run.status === "completed" ? formatScore(run.avg_answer_relevancy) : "—"}
                    </td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(run.avg_hallucination_risk, true)}`}>
                      {run.status === "completed" ? formatScore(run.avg_hallucination_risk) : "—"}
                    </td>

                    <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                      {run.avg_latency_ms ? `${run.avg_latency_ms.toFixed(0)}ms` : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                      {run.total_cost_usd != null ? `$${run.total_cost_usd.toFixed(4)}` : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                      {run.created_at ? format(new Date(run.created_at), "MMM dd HH:mm") : "—"}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {/* View */}
                        <Link href={`/dashboard/evaluation/${run.id}`}
                          className="p-1.5 rounded hover:bg-blue-50 text-blue-500 hover:text-blue-700 transition-colors"
                          title="View details">
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Link>

                        {/* Export — only for completed */}
                        {run.status === "completed" && (
                          <div className="relative group">
                            <button className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors" title="Export">
                              <Download className="h-3.5 w-3.5" />
                            </button>
                            <div className="absolute right-0 top-full mt-1 bg-white border rounded-lg shadow-xl z-20 hidden group-hover:block min-w-[100px]">
                              {(["csv", "excel", "pdf"] as const).map((fmt) => (
                                <button key={fmt} onClick={() => handleExport(run.id, fmt)}
                                  className="block w-full text-left px-3 py-2 text-xs hover:bg-gray-50 uppercase font-medium text-gray-600">
                                  {fmt}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Delete */}
                        <button
                          onClick={() => handleDelete(run.id, run.name)}
                          disabled={isDeleting || isRunning}
                          title={isRunning ? "Cannot delete a running evaluation" : "Delete this run"}
                          className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        >
                          {isDeleting
                            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            : <Trash2 className="h-3.5 w-3.5" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-5 py-4 border-t flex items-center justify-between bg-gray-50">
              <span className="text-xs text-gray-500">Page {page} of {totalPages} · {total} runs</span>
              <div className="flex gap-2">
                <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-40 hover:bg-white">← Prev</button>
                <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-40 hover:bg-white">Next →</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
