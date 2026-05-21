const API_BASE = import.meta.env.VITE_API_URL ?? "";

export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "cancelled"
  | "failed";

export interface GenerateOptions {
  controlnet_scale?: number;
  guidance_scale?: number;
}

export interface GenerateRequest {
  prompt: string;
  sketch: string;
  seed?: number;
  controlnet_scale?: number;
  guidance_scale?: number;
}

export interface GenerateJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface GenerateResultResponse {
  job_id: string;
  status: JobStatus;
  image?: string;
  error?: string;
  device?: string;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  device: string;
  peft_installed?: boolean;
  peft_backend?: boolean;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function submitGeneration(
  body: GenerateRequest,
  signal?: AbortSignal
): Promise<GenerateJobResponse> {
  const res = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error ?? "Generate failed");
  }
  return res.json();
}

export async function pollGeneration(
  jobId: string,
  signal?: AbortSignal,
  intervalMs = 300,
  maxAttempts = 300
): Promise<GenerateResultResponse> {
  for (let i = 0; i < maxAttempts; i++) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");

    const res = await fetch(`${API_BASE}/api/generate/${jobId}`, { signal });
    if (!res.ok) throw new Error("Poll failed");

    const data: GenerateResultResponse = await res.json();
    if (
      data.status === "completed" ||
      data.status === "failed" ||
      data.status === "cancelled"
    ) {
      return data;
    }

    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("Generation timed out");
}
