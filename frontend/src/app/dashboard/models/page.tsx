"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { modelsApi, evaluationApi } from "@/lib/api";
import { formatScore, scoreColor } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";

export default function ModelBenchmarkPage() {
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);

  const { data: historyData } = useQuery({
    queryKey: ["eval-history-all"],
    queryFn: () => evaluationApi.getHistory({ page_size: 100 }).then((r) => r.data),
  });

  const { data: compareData, refetch: runCompare } = useQuery({
    queryKey: ["model-compare", selectedRunIds],
    queryFn: () =>
      selectedRunIds.length > 0
        ? modelsApi.compare(selectedRunIds.join(",")).then((r) => r.data)
        : Promise.resolve({ comparison: [] }),
    enabled: selectedRunIds.length > 0,
  });

  const { data: fallbackData } = useQuery({
    queryKey: ["fallback-analytics"],
    queryFn: () => modelsApi.fallbackAnalytics().then((r) => r.data),
  });

  const runs = historyData?.runs?.filter((r: any) => r.status === "completed") || [];
  const comparison = compareData?.comparison || [];
  const fallbackEvents = fallbackData?.fallback_analytics || [];

  const radarData = comparison.map((c: any) => ({
    model: `${c.provider}/${c.model}`,
    Faithfulness: (c.faithfulness || 0) * 100,
    Relevancy: (c.answer_relevancy || 0) * 100,
    "Ctx Precision": (c.context_precision || 0) * 100,
    "Ctx Recall": (c.context_recall || 0) * 100,
  }));

  const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"];

  const toggleRun = (id: string) => {
    setSelectedRunIds((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Model Benchmarking</h1>
        <p className="text-gray-500 text-sm">Compare LLM providers side-by-side on RAGAS metrics</p>
      </div>

      {/* Run selector */}
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-semibold text-gray-800 mb-3">Select Evaluation Runs to Compare</h2>
        {runs.length === 0 ? (
          <p className="text-gray-400 text-sm">No completed evaluation runs found.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {runs.map((run: any) => (
              <button
                key={run.id}
                onClick={() => toggleRun(run.id)}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                  selectedRunIds.includes(run.id)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                {run.name} ({run.provider}/{run.model_name})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Comparison Table */}
      {comparison.length > 0 && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <h2 className="font-semibold text-gray-800 p-5 border-b">Side-by-Side Comparison</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Model", "Provider", "Faithfulness", "Relevancy", "Ctx Precision", "Ctx Recall", "Hallucination Risk", "Latency (ms)", "Cost (USD)", "Questions"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {comparison.map((c: any, i: number) => (
                  <tr key={c.run_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{c.model}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded capitalize">{c.provider}</span>
                    </td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(c.faithfulness)}`}>{formatScore(c.faithfulness)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(c.answer_relevancy)}`}>{formatScore(c.answer_relevancy)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(c.context_precision)}`}>{formatScore(c.context_precision)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(c.context_recall)}`}>{formatScore(c.context_recall)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(c.hallucination_risk, true)}`}>{formatScore(c.hallucination_risk)}</td>
                    <td className="px-4 py-3 text-gray-600">{c.avg_latency_ms?.toFixed(0) || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{c.total_cost_usd != null ? `$${c.total_cost_usd.toFixed(4)}` : "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{c.total_questions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Charts */}
      {comparison.length > 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Faithfulness Comparison</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={comparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="model" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                <Bar dataKey="faithfulness" name="Faithfulness" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="answer_relevancy" name="Relevancy" fill="#10B981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="hallucination_risk" name="Hallucination Risk" fill="#EF4444" radius={[4, 4, 0, 0]} />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar Chart */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-semibold text-gray-800 mb-4">Radar Comparison</h3>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData.length > 0 ? [
                { metric: "Faithfulness", ...Object.fromEntries(comparison.map((c: any) => [`${c.provider}/${c.model}`, (c.faithfulness || 0) * 100])) },
                { metric: "Relevancy", ...Object.fromEntries(comparison.map((c: any) => [`${c.provider}/${c.model}`, (c.answer_relevancy || 0) * 100])) },
                { metric: "Ctx Precision", ...Object.fromEntries(comparison.map((c: any) => [`${c.provider}/${c.model}`, (c.context_precision || 0) * 100])) },
                { metric: "Ctx Recall", ...Object.fromEntries(comparison.map((c: any) => [`${c.provider}/${c.model}`, (c.context_recall || 0) * 100])) },
              ] : []}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis domain={[0, 100]} />
                {comparison.map((c: any, i: number) => (
                  <Radar
                    key={c.run_id}
                    name={`${c.provider}/${c.model}`}
                    dataKey={`${c.provider}/${c.model}`}
                    stroke={COLORS[i % COLORS.length]}
                    fill={COLORS[i % COLORS.length]}
                    fillOpacity={0.1}
                  />
                ))}
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Fallback Analytics */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="font-semibold text-gray-800 mb-4">LLM Fallback Analytics</h2>
        {fallbackEvents.length === 0 ? (
          <p className="text-gray-400 text-sm">No fallback events recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {fallbackEvents.map((e: any) => (
              <div key={e.pair} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-800">{e.pair}</p>
                  <p className="text-xs text-gray-500">
                    Reasons: {Object.entries(e.reasons).map(([k, v]) => `${k}(${v})`).join(", ")}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{e.total_events} events</p>
                  <p className="text-xs text-gray-500">
                    {(e.success_rate * 100).toFixed(0)}% success
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
