import { ImageAsset, Job, MetricsResponse, TokenResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const STORAGE_SEGMENT = "backend\\storage";

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("gencloudnet.token");
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("gencloudnet.token", token);
  }
}

export function clearToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem("gencloudnet.token");
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(payload.detail ?? "Request failed");
  }

  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return apiRequest<TokenResponse>("/auth/token", { method: "POST", body });
}

export async function register(payload: { email: string; full_name: string; password: string }) {
  return apiRequest<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function fetchAssets() {
  return apiRequest<ImageAsset[]>("/uploads");
}

export async function uploadAsset(file: File, captureDate?: string) {
  const body = new FormData();
  body.append("file", file);
  if (captureDate) {
    body.append("capture_date", captureDate);
  }
  return apiRequest<{ asset: ImageAsset }>("/uploads", {
    method: "POST",
    body
  });
}

export async function fetchHistory() {
  return apiRequest<{ jobs: Job[] }>("/history");
}

export async function fetchMetrics() {
  return apiRequest<MetricsResponse>("/metrics");
}

export async function runPrediction(payload: {
  image_id: string;
  temporal_image_ids: string[];
  sar_image_id?: string;
  generator_model: string;
  super_resolution_model: string;
  enhance: boolean;
  use_deep_cloud_model: boolean;
  explainability: boolean;
}) {
  return apiRequest<Job>("/predict", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createCloudMask(imageId: string, modelName: string) {
  return apiRequest<Job>("/cloud-mask", {
    method: "POST",
    body: JSON.stringify({ image_id: imageId, model_name: modelName })
  });
}

export async function runFusion(payload: { image_id: string; temporal_image_ids: string[]; sar_image_id?: string }) {
  return apiRequest<Job>("/fusion", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function runSuperResolution(imageId: string, modelName: string) {
  return apiRequest<Job>("/super-resolution", {
    method: "POST",
    body: JSON.stringify({ image_id: imageId, model_name: modelName })
  });
}

export function toPublicFileUrl(path: string | null) {
  if (!path) {
    return null;
  }
  const normalized = path.replaceAll("/", "\\");
  const parts = normalized.split(STORAGE_SEGMENT);
  if (parts.length < 2) {
    return null;
  }
  return `http://localhost:8000/files${parts[1].replaceAll("\\", "/")}`;
}
