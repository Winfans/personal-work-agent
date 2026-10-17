import type { ApiResponse } from "./types";

const NOTES_URL = "http://127.0.0.1:8000/api/v1/notes";

export interface Note {
  id: number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface NoteInput {
  title: string;
  content: string;
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
  if (!response.ok || body.code !== 0) {
    throw new Error(body.message || `服务端返回 ${response.status}`);
  }
  return body.data;
};

export const listNotes = (signal?: AbortSignal): Promise<Note[]> => request<Note[]>(
  `${NOTES_URL}?offset=0&limit=100`,
  { signal },
);

export const createNote = (input: NoteInput): Promise<Note> => request<Note>(NOTES_URL, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(input),
});

export const updateNote = (id: number, input: NoteInput): Promise<Note> => request<Note>(
  `${NOTES_URL}/${id}`,
  {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  },
);

export const deleteNote = async (id: number): Promise<void> => {
  await request<null>(`${NOTES_URL}/${id}`, { method: "DELETE" });
};
