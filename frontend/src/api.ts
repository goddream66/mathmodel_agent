import type { ReportSection, SessionSummary } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function createSession(): Promise<SessionSummary> {
  return request<SessionSummary>("/api/sessions", { method: "POST" });
}

export async function getMeta(): Promise<{ sections: ReportSection[] }> {
  return request<{ sections: ReportSection[] }>("/api/meta");
}

export async function addMessage(sessionId: string, content: string): Promise<SessionSummary> {
  return request<SessionSummary>(`/api/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function uploadFiles(
  sessionId: string,
  role: "problem" | "data",
  files: File[],
): Promise<SessionSummary> {
  const formData = new FormData();
  formData.append("role", role);
  for (const file of files) {
    formData.append("files", file);
  }
  return request<SessionSummary>(`/api/sessions/${sessionId}/files`, {
    method: "POST",
    body: formData,
  });
}

export async function setSections(sessionId: string, sections: string[]): Promise<SessionSummary> {
  return request<SessionSummary>(`/api/sessions/${sessionId}/sections`, {
    method: "POST",
    body: JSON.stringify({ sections }),
  });
}

export async function runSession(sessionId: string, sections: string[]): Promise<SessionSummary> {
  return request<SessionSummary>(`/api/sessions/${sessionId}/run`, {
    method: "POST",
    body: JSON.stringify({ sections }),
  });
}
