"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { MetricCard } from "@/components/ui/metric-card";
import { formatScore, scoreColor } from "@/lib/utils";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import {
  Brain, Target, AlignLeft, Search,
  AlertTriangle, Clock, DollarSign, Database,
  FlaskConical, Zap, TrendingUp,
} from "lucide-react";
import { format } from "date-fns";

const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"];

export default function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => dashboardApi.summary().then((r) => r.data),
    refetchInterval: 30000,
  });

  const { data: trendsData } = useQuery({
    queryKey: ["dashboard-trends"],
    queryFn: () => dashboardApi.trends(30).then((r) => r.data),
  });

  const { data: modelUsage } = useQuery({
    queryKey: ["model-usage"],
    queryFn: () => dashboardApi.modelUsage().then((r) => r.data),
  });

  const trends = trendsData?.trends || [];
  const chartData = trends.map((t: any) => ({
    ...t,
    date: t.date ? format(new Date(t.date), "MMM dd") : "",
  }));

  const usageData = modelUsage?.model_usage || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics Overview</h1>
        <p className="text-gray-500 text-sm mt-1">
          Real-time RAG system performance and evaluation metrics
        </p>
      </div>

      {/* System KPIs */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          System Metrics
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            title="Total Evaluations"
            value={summary?.total_evaluations}
            icon={FlaskConical}
            rawValue
          />
          <MetricCard
            title="Total Queries"
            value={summary?.total_queries}
            icon={Search}
            rawValue
          />
          <MetricCard
            title="Total Datasets"
            value={summary?.total_datasets}
            icon={Database}
            rawValue
          />
          <MetricCard
            title="Fallback Events"
            value={summary?.total_fallback_events}
            icon={Zap}
            rawValue
          />
        </div>
      </section>

      {/* RAGAS Metrics */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          RAGAS Metrics (Avg across all runs)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <MetricCard title="Faithfulness" value={summary?.avg_faithfulness} icon={Brain} />
          <MetricCard title="Answer Relevancy" value={summary?.avg_answer_relevancy} icon={Target} />
          <MetricCard title="Context Precision" value={summary?.avg_context_precision} icon={AlignLeft} />
          <MetricCard title="Context Recall" value={summary?.avg_context_recall} icon={Search} />
          <MetricCard
            title="Hallucination Risk"
            value={summary?.avg_hallucination_risk}
            icon={AlertTriangle}
            invert
          />
          <MetricCard
            title="Avg Latency"
            value={summary?.avg_latency_ms}
            icon={Clock}
            rawValue
            suffix=" ms"
          />
        </div>
      </section>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Faithfulness + Relevancy Trend */}
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">RAGAS Metric Trends (30 days)</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                <Legend />
                <Line type="monotone" dataKey="faithfulness" stroke="#3B82F6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="answer_relevancy" stroke="#10B981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="context_precision" stroke="#F59E0B" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="context_recall" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="hallucination_risk" stroke="#EF4444" strokeWidth={2} dot={false} strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-400 text-sm">
              No evaluation data yet. Run your first evaluation to see trends.
            </div>
          )}
        </div>

        {/* Model Usage Pie */}
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">Model Usage Distribution</h3>
          {usageData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={usageData}
                  dataKey="count"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ label, percent }) => `${label} (${(percent * 100).toFixed(0)}%)`}
                >
                  {usageData.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-400 text-sm">
              No model usage data yet.
            </div>
          )}
        </div>
      </div>

      {/* Latency Bar Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">Latency per Evaluation Run (ms)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="run_name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="latency_ms" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
