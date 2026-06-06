import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return (score * 100).toFixed(1) + "%";
}

export function scoreColor(score: number | null | undefined, invert = false): string {
  if (score === null || score === undefined) return "text-gray-400";
  const val = invert ? 1 - score : score;
  if (val >= 0.8) return "text-green-600";
  if (val >= 0.6) return "text-yellow-600";
  return "text-red-600";
}

export function scoreBg(score: number | null | undefined, invert = false): string {
  if (score === null || score === undefined) return "bg-gray-100";
  const val = invert ? 1 - score : score;
  if (val >= 0.8) return "bg-green-100";
  if (val >= 0.6) return "bg-yellow-100";
  return "bg-red-100";
}

export function downloadBlob(data: Blob, filename: string) {
  const url = window.URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
