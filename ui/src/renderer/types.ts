export type Role = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
}

export interface AgentMessage {
  role: Role;
  content: string;
}

export interface StreamEvent {
  type: "start" | "route" | "retrieval" | "delta" | "done" | "error";
  model?: string;
  content?: string;
  message?: string;
  route?: "general_chat" | "rag_chat";
  confidence?: number;
  count?: number;
}
