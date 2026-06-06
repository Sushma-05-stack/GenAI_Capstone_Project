"use client";

import { useQuery } from "@tanstack/react-query";
import { securityApi } from "@/lib/api";
import { format } from "date-fns";
import { Shield, AlertTriangle, LogIn, Zap } from "lucide-react";

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

export default function SecurityPage() {
  const { data: stats } = useQuery({
    queryKey: ["security-stats"],
    queryFn: () => securityApi.getStats().then((r) => r.data),
  });

  const { data: logsData } = useQuery({
    queryKey: ["security-logs"],
    queryFn: () => securityApi.getLogs({ page_size: 50 }).then((r) => r.data),
  });

  const logs = logsData?.logs || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Security Logs</h1>
        <p className="text-gray-500 text-sm">Audit trail and security event monitoring</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Events", value: stats?.total_audit_events, icon: Shield, color: "text-blue-600" },
          { label: "High Risk Events", value: stats?.high_risk_events, icon: AlertTriangle, color: "text-red-600" },
          { label: "Failed Logins", value: stats?.failed_logins, icon: LogIn, color: "text-yellow-600" },
          { label: "Injection Attempts", value: stats?.injection_attempts, icon: Zap, color: "text-purple-600" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{s.label}</span>
              <s.icon className={`h-4 w-4 ${s.color}`} />
            </div>
            <p className={`text-2xl font-bold ${s.color}`}>{s.value ?? "—"}</p>
          </div>
        ))}
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="p-5 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Recent Audit Events</h2>
          <span className="text-xs text-gray-400">{logsData?.total || 0} total events</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Timestamp", "Action", "User ID", "IP Address", "Risk", "Status", "Details"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {logs.map((log: any) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {log.created_at ? format(new Date(log.created_at), "MMM dd HH:mm:ss") : "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{log.action}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">{log.user_id ? log.user_id.slice(-8) : "—"}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{log.ip_address || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${RISK_COLORS[log.risk_level] || ""}`}>
                      {log.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${log.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {log.success ? "success" : "failed"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-[200px] truncate">
                    {JSON.stringify(log.details)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
