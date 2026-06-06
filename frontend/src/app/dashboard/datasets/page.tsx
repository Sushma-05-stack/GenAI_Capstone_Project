"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { datasetsApi } from "@/lib/api";
import { useToast } from "@/components/ui/toaster";
import { Plus, Upload, Trash2, FileText, Search, Tag } from "lucide-react";
import { format } from "date-fns";
import { RoleErrorBanner } from "@/components/ui/role-error-banner";

const STATUS_COLORS: Record<string, string> = {
  processing: "bg-blue-100 text-blue-700",
  ready: "bg-green-100 text-green-700",
  error: "bg-red-100 text-red-700",
};

export default function DatasetsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [uploadDatasetId, setUploadDatasetId] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["datasets", search],
    queryFn: () => datasetsApi.list({ search, page_size: 50 }).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => datasetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      toast({ title: "Dataset created" });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
    },
    onError: (e: any) => {
      const detail = e.response?.data?.detail || "Unknown error";
      const msg = detail.includes("role")
        ? "Your session role is outdated. Please log out and log back in."
        : detail;
      toast({ title: "Error creating dataset", description: msg, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => datasetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      toast({ title: "Dataset deleted" });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) =>
      datasetsApi.uploadFile(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      toast({ title: "File uploaded", description: "Processing started in background" });
      setUploadDatasetId("");
      setUploadFile(null);
    },
    onError: (e: any) =>
      toast({ title: "Upload failed", description: e.response?.data?.detail, variant: "destructive" }),
  });

  const datasets = data?.datasets || [];

  return (
    <div className="space-y-6">
      <RoleErrorBanner error={createMutation.error || deleteMutation.error || uploadMutation.error} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
          <p className="text-gray-500 text-sm">Manage your evaluation datasets and documents</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" /> New Dataset
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search datasets..."
        />
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h2 className="font-bold text-lg mb-4">Create Dataset</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="My Dataset"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">
                  Cancel
                </button>
                <button
                  onClick={() => createMutation.mutate({ name: newName, description: newDesc })}
                  disabled={!newName || createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? "Creating..." : "Create"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {uploadDatasetId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h2 className="font-bold text-lg mb-4">Upload Document</h2>
            <div className="space-y-4">
              <div className="border-2 border-dashed rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-sm"
                />
                <p className="text-xs text-gray-400 mt-2">PDF, DOCX, TXT, CSV (max 50MB)</p>
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => { setUploadDatasetId(""); setUploadFile(null); }} className="px-4 py-2 text-sm border rounded-lg">
                  Cancel
                </button>
                <button
                  onClick={() => uploadFile && uploadMutation.mutate({ id: uploadDatasetId, file: uploadFile })}
                  disabled={!uploadFile || uploadMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg disabled:opacity-50"
                >
                  {uploadMutation.isPending ? "Uploading..." : "Upload"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Grid */}
      {isLoading ? (
        <div className="text-center py-20 text-gray-400">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((d: any) => (
            <div key={d.id} className="bg-white rounded-xl border p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-500" />
                  <span className="font-semibold text-gray-900 text-sm">{d.name}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[d.status]}`}>
                  {d.status}
                </span>
              </div>
              {d.description && (
                <p className="text-xs text-gray-500 mb-3 line-clamp-2">{d.description}</p>
              )}
              <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                <span>{d.file_count} files</span>
                <span>{d.qa_count} QA pairs</span>
                <span>v{d.version}</span>
              </div>
              {d.tags?.length > 0 && (
                <div className="flex gap-1 flex-wrap mb-3">
                  {d.tags.map((tag: string) => (
                    <span key={tag} className="flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                      <Tag className="h-2.5 w-2.5" />{tag}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-between pt-3 border-t">
                <span className="text-xs text-gray-400">
                  {d.created_at ? format(new Date(d.created_at), "MMM dd, yyyy") : ""}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setUploadDatasetId(d.id)}
                    className="p-1.5 rounded hover:bg-blue-50 text-blue-600"
                    title="Upload document"
                  >
                    <Upload className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm("Delete this dataset?")) deleteMutation.mutate(d.id);
                    }}
                    className="p-1.5 rounded hover:bg-red-50 text-red-500"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
