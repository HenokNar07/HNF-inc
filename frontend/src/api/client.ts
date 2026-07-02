import type { AnalyzeRequest, MVOResult } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // FastAPI's error handlers (see backend/app/main.py) always return
    // {"detail": "..."} -- for 422s (pydantic validation) detail is a list
    // instead of a string, so normalize both shapes to one message.
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ")
      : (detail ?? response.statusText);
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<TResponse>;
}

export function analyzePortfolio(request: AnalyzeRequest): Promise<MVOResult> {
  return postJson<MVOResult>("/api/analyze", request);
}

export function explainResult(result: MVOResult): Promise<string> {
  return postJson<{ explanation: string }>("/api/explain", { result }).then(
    (res) => res.explanation
  );
}
