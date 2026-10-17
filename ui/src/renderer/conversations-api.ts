import type { ApiResponse } from "./types";

const URL = "http://127.0.0.1:8000/api/v1/conversations";

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface StoredMessage {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

const request = async <T>(url: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(url, init);
  let body: ApiResponse<T>;
  try {
    body = await response.json() as ApiResponse<T>;
  } catch {
    throw new Error(`服务端返回 ${response.status}，响应不是有效的 JSON`);
  }
  if (typeof body?.code !== "number" || typeof body.message !== "string" || !("data" in body)) {
    throw new Error("服务端响应格式错误");
  }
  if (!response.ok || body.code !== 0) throw new Error(body.message);
  return body.data;
};

export const listConversations = (beforeId?: number, signal?: AbortSignal): Promise<Conversation[]> => {
  const query = new URLSearchParams({ limit: "30" });
  if (beforeId !== undefined) query.set("before_id", String(beforeId));
  return request<Conversation[]>(`${URL}?${query}`, { signal });
};

export const createConversation = (title: string): Promise<Conversation> => request<Conversation>(URL, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title }),
});

export const listMessages = (
  conversationId: number,
  beforeId?: number,
  signal?: AbortSignal,
): Promise<StoredMessage[]> => {
  const query = new URLSearchParams({ limit: "50" });
  if (beforeId !== undefined) query.set("before_id", String(beforeId));
  return request<StoredMessage[]>(`${URL}/${conversationId}/messages?${query}`, { signal });
};
