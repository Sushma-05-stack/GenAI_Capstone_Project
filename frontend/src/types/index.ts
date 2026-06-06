export interface EvaluationRun {
  id: string;
  name: string;
  dataset_id: string;
  owner_id: string;
  model_name: string;
  provider: string;
  status: "pending" | "running" | "completed" | "failed";
  total_questions: number;
  completed_questions: number;
  avg_faithfulness: number | null;
  avg_answer_relevancy: number | null;
  avg_context_precision: number | null;
  avg_context_recall: number | null;
  avg_hallucination_risk: number | null;
  avg_retrieval_quality: number | null;
  avg_latency_ms: number | null;
  total_cost_usd: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface EvaluationResult {
  id: string;
  run_id: string;
  question: string;
  answer: string;
  ground_truth: string | null;
  contexts: string[];
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  context_recall: number | null;
  hallucination_risk: number | null;
  retrieval_quality: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
  model_used: string;
  provider_used: string;
  fallback_used: boolean;
  langsmith_trace_url: string | null;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  version: string;
  status: "processing" | "ready" | "error";
  file_count: number;
  qa_count: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  id: string;
  name: string;
  version: string;
  content: string;
  description: string | null;
  owner_id: string;
  is_active: boolean;
  tags: string[];
  avg_faithfulness: number | null;
  avg_answer_relevancy: number | null;
  avg_latency_ms: number | null;
  eval_count: number;
  created_at: string;
}

export interface DashboardSummary {
  total_evaluations: number;
  completed_evaluations: number;
  total_queries: number;
  total_datasets: number;
  total_fallback_events: number;
  avg_faithfulness: number | null;
  avg_answer_relevancy: number | null;
  avg_context_precision: number | null;
  avg_context_recall: number | null;
  avg_hallucination_risk: number | null;
  avg_latency_ms: number | null;
  avg_cost_usd: number | null;
}

export interface TrendDataPoint {
  date: string;
  run_name: string;
  model: string;
  provider: string;
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  context_recall: number | null;
  hallucination_risk: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
}
