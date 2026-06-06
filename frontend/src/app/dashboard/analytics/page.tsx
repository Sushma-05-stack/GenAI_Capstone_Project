"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi, evaluationApi } from "@/lib/api";
import {
  LineChart, Line, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Cell,
} from "recharts";
import { formatScore, scoreColor } from "@/lib/utils";
import { format } from "date-fns";
import { Brain, Target, AlertTriangle, Search, AlignLeft, Zap } from "lucide-react";

const METRIC_COLORS = {
  faithfulness:       "#3B82F6",
  answer_relevancy:   "#10B981",
  context_precision:  "#F59E0B",
  context_recall:     "#8B5CF6",
  hallucination_risk: "#EF4444",
  retrieval_quality:  "#06B6D4",
};

// Custom dot that colors itself based on value
const ScoreDot = (props: any) => {
  const { cx, cy, value } = props;
  if (value == null) return null;
  const color = value >= 80 ? "#10B981" : value >= 60 ? "#F59E0B" : "#EF4444";
  return <circle cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={2} />;
};

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [activeMetrics, setActiveMetrics] = useState<Set<string>>(
    new Set(["faithfulness", "answer_relevancy", "hallucination_risk"])
  );

  const { data: trendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ["trends", days],
    queryFn: () => dashboardApi.trends(days).then((r) => r.data),
  });

  const { data: hallData } = useQuery({
    queryKey: ["hallucination-report", days],
    queryFn: () => dashboardApi.hallucinationReport(days).then((r) => r.data),
  });

  const { data: evalHistory } = useQuery({
    queryKey: ["eval-history-analytics"],
    queryFn: () => evaluationApi.getHistory({ page_size: 50 }).then((r) => r.data),
  });

  const completedRuns = (evalHistory?.runs || []).filter(
    (r: any) => r.status === "completed"
  );

  // Build trend chart data — one point per completed run
  const trends = (trendsData?.trends || []).map((t: any) => ({
    ...t,
    date: t.date ? format(new Date(t.date), "MMM dd HH:mm") : "",
    label: t.run_name || "Run",
    faithfulness:      t.faithfulness      != null ? +(t.faithfulness      * 100).toFixed(1) : null,
    answer_relevancy:  t.answer_relevancy  != null ? +(t.answer_relevancy  * 100).toFixed(1) : null,
    context_precision: t.context_precision != null ? +(t.context_precision * 100).toFixed(1) : null,
    context_recall:    t.context_recall    != null ? +(t.context_recall    * 100).toFixed(1) : null,
    hallucination_risk:t.hallucination_risk!= null ? +(t.hallucination_risk* 100).toFixed(1) : null,
    latency_ms: t.latency_ms,
    cost_usd: t.cost_usd,
  }));

  // Radar data from the most recent completed run
  const latestRun = completedRuns[0];
  const radarData = latestRun ? [
    { metric: "Faithfulness",       A: (latestRun.avg_faithfulness       ?? 0) * 100 },
    { metric: "Relevancy",          A: (latestRun.avg_answer_relevancy   ?? 0) * 100 },
    { metric: "Ctx Precision",      A: (latestRun.avg_context_precision  ?? 0) * 100 },
    { metric: "Ctx Recall",         A: (latestRun.avg_context_recall     ?? 0) * 100 },
    { metric: "Low Hallucination",  A: (1 - (latestRun.avg_hallucination_risk ?? 0)) * 100 },
  ] : [];

  // Metric score distribution across all completed runs
  const scoreDistribution = completedRuns.map((r: any) => ({
    name: r.name.length > 16 ? r.name.slice(0, 14) + "…" : r.name,
    faithfulness:      r.avg_faithfulness      != null ? +(r.avg_faithfulness      * 100).toFixed(1) : 0,
    answer_relevancy:  r.avg_answer_relevancy  != null ? +(r.avg_answer_relevancy  * 100).toFixed(1) : 0,
    hallucination_risk:r.avg_hallucination_risk!= null ? +(r.avg_hallucination_risk* 100).toFixed(1) : 0,
  }));

  const highRisk = hallData?.results || [];

  const toggleMetric = (key: string) => {
    setActiveMetrics((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const hasData = trends.length > 0;
  const hasRuns = completedRuns.length > 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            RAGAS metrics from <strong>completed evaluation runs</strong> — not individual RAG queries
          </p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Explanation banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl px-5 py-4">
        <p className="text-sm text-blue-800 font-medium">
          How to populate these charts
        </p>
        <p className="text-xs text-blue-600 mt-1">
          Go to <strong>Evaluations → New Evaluation</strong>, select a dataset with QA pairs, choose a model, and run it.
          Each completed evaluation run adds one data point to every chart below.
          RAGAS scores (faithfulness, hallucination risk, etc.) are computed per run, not per RAG query.
        </p>
      </div>

      {/* ── RAGAS Metric Trends ───────────────────────────── */}
      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-800">RAGAS Metric Trends per Evaluation Run</h2>
          <span className="text-xs text-gray-400">{trends.length} data points</span>
        </div>

        {/* Metric toggles */}
        <div className="flex flex-wrap gap-2 mb-5">
          {(Object.entries(METRIC_COLORS) as [string, string][]).map(([key, color]) => (
            <button
              key={key}
              onClick={() => toggleMetric(key)}
              className={`text-xs px-3 py-1 rounded-full border transition-all font-medium ${
                activeMetrics.has(key)
                  ? "text-white border-transparent"
                  : "bg-white text-gray-500 border-gray-200"
              }`}
              style={activeMetrics.has(key) ? { background: color } : {}}
            >
              {key.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {!hasData ? (
          <div className="h-[320px] flex flex-col items-center justify-center gap-3 text-gray-400">
            <Brain className="h-10 w-10 opacity-30" />
            <p className="text-sm font-medium">No completed evaluation runs yet</p>
            <p className="text-xs">Run an evaluation from the Evaluations page to see data here</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trends} margin={{ left: 0, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                formatter={(v: number, name: string) => [`${v?.toFixed(1)}%`, name.replace(/_/g, " ")]}
                labelFormatter={(l) => `Run: ${l}`}
                contentStyle={{ fontSize: 12 }}
              />
              <ReferenceLine y={80} stroke="#10B981" strokeDasharray="4 2" strokeOpacity={0.4} label={{ value: "Good ≥80%", fontSize: 10, fill: "#10B981" }} />
              <ReferenceLine y={60} stroke="#F59E0B" strokeDasharray="4 2" strokeOpacity={0.4} label={{ value: "Fair ≥60%", fontSize: 10, fill: "#F59E0B" }} />
              <Legend formatter={(v) => v.replace(/_/g, " ")} />
              {(Object.entries(METRIC_COLORS) as [string, string][]).map(([key, color]) =>
                activeMetrics.has(key) ? (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    name={key}
                    stroke={color}
                    strokeWidth={2.5}
                    dot={<ScoreDot />}
                    connectNulls={false}
                  />
                ) : null
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Two-column: Radar + Score Distribution ────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar — latest run */}
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-1">Latest Run — Quality Radar</h2>
          <p className="text-xs text-gray-400 mb-4">
            {latestRun ? `"${latestRun.name}" · ${latestRun.provider}/${latestRun.model_name}` : "No completed runs yet"}
          </p>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E5E7EB" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} tickCount={4} />
                <Radar
                  name="Score"
                  dataKey="A"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.25}
                  dot={{ r: 4, fill: "#3B82F6" }}
                />
                <Tooltip formatter={(v: number) => `${v?.toFixed(1)}%`} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-gray-300 text-sm">
              Run an evaluation to see the radar chart
            </div>
          )}
        </div>

        {/* Score distribution across runs */}
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-1">Score Comparison Across Runs</h2>
          <p className="text-xs text-gray-400 mb-4">Faithfulness vs Relevancy vs Hallucination Risk per run</p>
          {scoreDistribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={scoreDistribution} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v: number) => `${v?.toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="faithfulness"       name="Faithfulness"      fill="#3B82F6" radius={[0, 4, 4, 0]} />
                <Bar dataKey="answer_relevancy"   name="Relevancy"         fill="#10B981" radius={[0, 4, 4, 0]} />
                <Bar dataKey="hallucination_risk" name="Hallucination Risk" fill="#EF4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-gray-300 text-sm">
              No completed runs to compare
            </div>
          )}
        </div>
      </div>

      {/* ── Latency & Cost ─────────────────────────────────── */}
      {hasData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-4">Avg Latency per Run (ms)</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v?.toFixed(0)}ms`, "Latency"]} />
                <Bar dataKey="latency_ms" name="Latency (ms)" radius={[4, 4, 0, 0]}>
                  {trends.map((_: any, i: number) => (
                    <Cell key={i} fill={i % 2 === 0 ? "#3B82F6" : "#60A5FA"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-4">Total Cost per Run (USD)</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(v: number) => [`$${v?.toFixed(5)}`, "Cost"]} />
                <Bar dataKey="cost_usd" name="Cost (USD)" radius={[4, 4, 0, 0]}>
                  {trends.map((_: any, i: number) => (
                    <Cell key={i} fill={i % 2 === 0 ? "#10B981" : "#34D399"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── Hallucination Risk Report ────────────────────── */}
      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-semibold text-gray-800">Hallucination Risk Report</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Results where hallucination risk ≥ 50% (faithfulness &lt; 50%) — from evaluation runs only
            </p>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            highRisk.length > 0 ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
          }`}>
            {highRisk.length > 0 ? `${highRisk.length} flagged` : "All clear"}
          </span>
        </div>
        {highRisk.length === 0 ? (
          <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg border border-green-100">
            <AlertTriangle className="h-5 w-5 text-green-500" />
            <p className="text-sm text-green-700">
              No high-risk hallucinations detected. Complete more evaluation runs to monitor.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {highRisk.map((r: any) => (
              <div key={r.id} className="flex items-start gap-4 p-3 bg-red-50 rounded-lg border border-red-100">
                <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{r.question}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {r.model_used} · {r.created_at ? format(new Date(r.created_at), "MMM dd HH:mm") : ""}
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-sm font-bold text-red-600">{formatScore(r.hallucination_risk)}</p>
                  <p className="text-xs text-gray-500">Faith: {formatScore(r.faithfulness)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Completed Runs Summary Table ─────────────────── */}
      {hasRuns && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <div className="p-5 border-b">
            <h2 className="font-semibold text-gray-800">All Evaluation Runs Summary</h2>
            <p className="text-xs text-gray-400 mt-0.5">{completedRuns.length} completed run(s)</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Run", "Model", "Faithful", "Relevancy", "Ctx Prec", "Ctx Recall", "Hall. Risk", "Latency", "Cost", "Qs"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {completedRuns.map((r: any) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800 max-w-[140px] truncate">{r.name}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{r.provider}/{r.model_name}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(r.avg_faithfulness)}`}>{formatScore(r.avg_faithfulness)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(r.avg_answer_relevancy)}`}>{formatScore(r.avg_answer_relevancy)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(r.avg_context_precision)}`}>{formatScore(r.avg_context_precision)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(r.avg_context_recall)}`}>{formatScore(r.avg_context_recall)}</td>
                    <td className={`px-4 py-3 font-medium ${scoreColor(r.avg_hallucination_risk, true)}`}>{formatScore(r.avg_hallucination_risk)}</td>
                    <td className="px-4 py-3 text-gray-500">{r.avg_latency_ms ? `${r.avg_latency_ms.toFixed(0)}ms` : "—"}</td>
                    <td className="px-4 py-3 text-gray-500">{r.total_cost_usd != null ? `$${r.total_cost_usd.toFixed(4)}` : "—"}</td>
                    <td className="px-4 py-3 text-gray-500">{r.total_questions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
