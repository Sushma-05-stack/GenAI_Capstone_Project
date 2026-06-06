"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { evaluationApi, feedbackApi, reportsApi } from "@/lib/api";
import { formatScore, scoreColor, scoreBg, downloadBlob } from "@/lib/utils";
import {
  ArrowLeft, Download, ExternalLink, ThumbsUp, ThumbsDown, Flag,
} from "lucide-react";
import { format } from "date-fns";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function EvalRunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const [page, setPage] = useState(1);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const { data: run, isLoading: runLoading } = useQuery({
    queryKey: ["eval-run", runId],
    queryFn: () => evaluationApi.getRun(runId).then((r) => r.data),
    refetchInterval: (q) =>
      q.state.data?.status === "running" ? 5000 : false,
  });

  const { data: resultsData } = useQuery({
    queryKey: ["eval-results", runId, page],
    queryFn: () =>
      evaluationApi.getResults(runId, { page, page_size: 20 }).then((r) => r.data),
    enabled: !!runId,
  });

  const { data: feedbackData } = useQuery({
    queryKey: ["run-feedback", runId],
    queryFn: () => feedbackApi.getForRun(runId).then((r) => r.data),
  });

  const results = resultsData?.results || [];
  const totalResults = resultsData?.total || 0;
  const totalPages = Math.ceil(totalResults / 20);

  const handleExport = async (fmt: "csv" | "excel" | "pdf") => {
    const fnMap = {
      csv: [reportsApi.exportCsv, `eval_${runId}.csv`],
      excel: [reportsApi.exportExcel, `eval_${runId}.xlsx`],
      pdf: [reportsApi.exportPdf, `eval_${runId}.pdf`],
    } as const;
    const [fn, filename] = fnMap[fmt];
    const res = await fn(runId);
    downloadBlob(res.data, filename);
  };

  const metricsBarData = run
    ? [
        { name: "Faithfulness", value: run.avg_faithfulness },
        { name: "Relevancy", value: run.avg_answer_relevancy },
        { name: "Ctx Precision", value: run.avg_context_precision },
        { name: "Ctx Recall", value: run.avg_context_recall },
        { name: "Hallucination Risk", value: run.avg_hallucination_risk },
        { name: "Retrieval Quality", value: run.avg_retrieval_quality },
      ].filter((d) => d.value != null)
    : [];

  if (runLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!run) return <p className="text-gray-500">Run not found.</p>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard/evaluation" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">{run.name}</h1>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[run.status] || ""}`}
              >
                {run.status}
                {run.status === "running" &&
                  ` (${run.completed_questions}/${run.total_questions})`}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              {run.provider} / {run.model_name} •{" "}
              {run.created_at
                ? format(new Date(run.created_at), "MMM dd, yyyy HH:mm")
                : ""}
            </p>
          </div>
        </div>
        {run.status === "completed" && (
          <div className="flex gap-2">
            {(["csv", "excel", "pdf"] as const).map((fmt) => (
              <button
                key={fmt}
                onClick={() => handleExport(fmt)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded-lg hover:bg-gray-50 uppercase font-medium"
              >
                <Download className="h-3.5 w-3.5" />
                {fmt}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Metrics Summary Cards */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {[
          { label: "Faithfulness", value: run.avg_faithfulness },
          { label: "Relevancy", value: run.avg_answer_relevancy },
          { label: "Ctx Precision", value: run.avg_context_precision },
          { label: "Ctx Recall", value: run.avg_context_recall },
          {
            label: "Hallucination",
            value: run.avg_hallucination_risk,
            invert: true,
          },
          {
            label: "Latency",
            value: run.avg_latency_ms,
            raw: true,
            suffix: "ms",
          },
        ].map((m) => (
          <div key={m.label} className="bg-white rounded-xl border p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">{m.label}</p>
            <p
              className={`text-xl font-bold ${
                m.raw ? "text-gray-800" : scoreColor(m.value, m.invert)
              }`}
            >
              {m.value == null
                ? "—"
                : m.raw
                ? `${m.value.toFixed(0)}${m.suffix}`
                : formatScore(m.value)}
            </p>
          </div>
        ))}
      </div>

      {/* Bar Chart */}
      {metricsBarData.length > 0 && (
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">
            Metrics Overview
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={metricsBarData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
              <Bar
                dataKey="value"
                fill="#3B82F6"
                radius={[0, 4, 4, 0]}
                label={{
                  position: "right",
                  formatter: (v: number) => `${(v * 100).toFixed(1)}%`,
                  fontSize: 11,
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Feedback Summary */}
      {feedbackData && feedbackData.total_feedback > 0 && (
        <div className="bg-white rounded-xl border p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-3">User Feedback</h2>
          <div className="flex gap-6 text-sm">
            <div>
              <span className="text-gray-500">Total feedback: </span>
              <span className="font-medium">{feedbackData.total_feedback}</span>
            </div>
            <div>
              <span className="text-gray-500">Avg rating: </span>
              <span className="font-medium">
                {feedbackData.avg_rating ?? "—"} / 5
              </span>
            </div>
            <div>
              <span className="text-gray-500">Hallucination flags: </span>
              <span className="font-medium text-red-600">
                {feedbackData.hallucination_flags}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Retrieval issues: </span>
              <span className="font-medium text-yellow-600">
                {feedbackData.retrieval_issues}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Per-question Results */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="p-5 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">
            Per-Question Results
          </h2>
          <span className="text-xs text-gray-400">{totalResults} questions</span>
        </div>

        {results.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">
            {run.status === "running"
              ? "Results appearing as evaluation runs..."
              : "No results yet."}
          </div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {[
                    "#",
                    "Question",
                    "Faithful",
                    "Relevancy",
                    "Hallucination",
                    "Latency",
                    "Model",
                    "Fallback",
                    "Trace",
                    "Details",
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {results.map((r: any, idx: number) => (
                  <>
                    <tr
                      key={r.id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() =>
                        setExpandedRow(expandedRow === r.id ? null : r.id)
                      }
                    >
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {(page - 1) * 20 + idx + 1}
                      </td>
                      <td className="px-4 py-3 max-w-[200px] truncate text-gray-800">
                        {r.question}
                      </td>
                      <td
                        className={`px-4 py-3 font-medium ${scoreColor(r.faithfulness)}`}
                      >
                        {formatScore(r.faithfulness)}
                      </td>
                      <td
                        className={`px-4 py-3 font-medium ${scoreColor(r.answer_relevancy)}`}
                      >
                        {formatScore(r.answer_relevancy)}
                      </td>
                      <td
                        className={`px-4 py-3 font-medium ${scoreColor(r.hallucination_risk, true)}`}
                      >
                        {formatScore(r.hallucination_risk)}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {r.latency_ms ? `${r.latency_ms.toFixed(0)}ms` : "—"}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <span className="bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                          {r.provider_used}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {r.fallback_used ? (
                          <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">
                            yes
                          </span>
                        ) : (
                          <span className="text-xs text-gray-300">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {r.langsmith_trace_url ? (
                          <a
                            href={r.langsmith_trace_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-blue-500 hover:text-blue-700"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {expandedRow === r.id ? "▲" : "▼"}
                      </td>
                    </tr>

                    {/* Expanded detail row */}
                    {expandedRow === r.id && (
                      <tr key={`${r.id}-detail`}>
                        <td colSpan={10} className="px-6 py-4 bg-blue-50 border-b border-blue-100">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs font-semibold text-gray-600 mb-1">
                                Answer
                              </p>
                              <p className="text-sm text-gray-700 bg-white p-3 rounded-lg border leading-relaxed">
                                {r.answer}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs font-semibold text-gray-600 mb-1">
                                Ground Truth
                              </p>
                              <p className="text-sm text-gray-700 bg-white p-3 rounded-lg border leading-relaxed">
                                {r.ground_truth || "Not provided"}
                              </p>
                            </div>
                            {r.contexts?.length > 0 && (
                              <div className="md:col-span-2">
                                <p className="text-xs font-semibold text-gray-600 mb-2">
                                  Retrieved Contexts ({r.contexts.length})
                                </p>
                                <div className="space-y-2">
                                  {r.contexts.map(
                                    (ctx: string, ci: number) => (
                                      <div
                                        key={ci}
                                        className="text-xs bg-white p-2.5 rounded border text-gray-600 leading-relaxed"
                                      >
                                        <span className="font-medium text-gray-400">
                                          #{ci + 1}:{" "}
                                        </span>
                                        {ctx.slice(0, 300)}
                                        {ctx.length > 300 ? "..." : ""}
                                      </div>
                                    )
                                  )}
                                </div>
                              </div>
                            )}
                            <div className="md:col-span-2 flex gap-6 text-xs text-gray-500">
                              <span>
                                Ctx Precision:{" "}
                                <b className={scoreColor(r.context_precision)}>
                                  {formatScore(r.context_precision)}
                                </b>
                              </span>
                              <span>
                                Ctx Recall:{" "}
                                <b className={scoreColor(r.context_recall)}>
                                  {formatScore(r.context_recall)}
                                </b>
                              </span>
                              <span>
                                Retrieval Quality:{" "}
                                <b className={scoreColor(r.retrieval_quality)}>
                                  {formatScore(r.retrieval_quality)}
                                </b>
                              </span>
                              <span>
                                Cost:{" "}
                                <b>
                                  {r.cost_usd
                                    ? `$${r.cost_usd.toFixed(5)}`
                                    : "—"}
                                </b>
                              </span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-5 py-4 border-t flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  Page {page} of {totalPages}
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage((p) => p - 1)}
                    className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-40 hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <button
                    disabled={page === totalPages}
                    onClick={() => setPage((p) => p + 1)}
                    className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-40 hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
