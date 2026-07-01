export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "analyst" | "operator";
  is_active: boolean;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type ImageAsset = {
  id: string;
  filename: string;
  source_path: string;
  preview_path: string | null;
  content_type: string;
  width: number;
  height: number;
  band_count: number;
  dtype: string;
  crs: string | null;
  transform_json: number[] | null;
  bounds_json: { left: number; bottom: number; right: number; top: number } | null;
  capture_date: string | null;
  cloud_coverage: number | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type Job = {
  id: string;
  image_id: string;
  status: "pending" | "running" | "completed" | "failed";
  task_type: string;
  generator_model: string;
  super_resolution_model: string | null;
  pipeline_config_json: Record<string, unknown>;
  result_path: string | null;
  fused_path: string | null;
  mask_path: string | null;
  confidence_path: string | null;
  explainability_path: string | null;
  metrics_json: Record<string, number>;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
};

export type MetricsResponse = {
  cloud_percentage_mean: number;
  average_processing_seconds: number;
  completed_jobs: number;
  failed_jobs: number;
  metric_summary: Record<string, number>;
};
