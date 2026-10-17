import { FormEvent, KeyboardEvent, useEffect, useLayoutEffect, useRef, useState } from "react";

import { streamAgentReply } from "./agent-api";
import NotesPage from "./NotesPage";
import type { AgentMessage, ChatMessage, StreamEvent } from "./types";

const IDLE_STATUS = "DeepSeek v4.1 · Streamable HTTP";
const suggestions = [
  { label: "梳理今日重点", prompt: "帮我梳理今天最重要的三项工作" },
  { label: "制定执行计划", prompt: "帮我把一个模糊想法整理成执行计划" },
  { label: "分析复杂问题", prompt: "帮我分析一个复杂问题并给出建议" },
] as const;

const newMessage = (role: ChatMessage["role"], content: string): ChatMessage => ({
  id: crypto.randomUUID(),
  role,
  content,
});

const statusForEvent = (event: StreamEvent): string | null => {
  if (event.type === "route") {
    return event.route === "rag_chat"
      ? "Jev 已选择知识库问答，正在召回…"
      : "Jev 已选择普通聊天，正在生成…";
  }
  if (event.type === "retrieval") {
    return `百炼已召回 ${event.count ?? 0} 条知识，正在生成…`;
  }
  if (event.type === "delta") return "DeepSeek 正在回答…";
  return null;
};

export default function App() {
  const [activeView, setActiveView] = useState<"chat" | "notes">("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState(IDLE_STATUS);
  const [conversationTitle, setConversationTitle] = useState("新对话");
  const messagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const requestRef = useRef<AbortController | null>(null);

  useLayoutEffect(() => {
    const element = messagesRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messages]);

  useEffect(() => () => requestRef.current?.abort(), []);

  const resizeComposer = (): void => {
    const element = textareaRef.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 180)}px`;
  };

  const updateAssistant = (id: string, content: string, append = true): void => {
    setMessages((current) => current.map((message) => (
      message.id === id
        ? { ...message, content: append ? message.content + content : content }
        : message
    )));
  };

  const submitMessage = async (): Promise<void> => {
    const content = input.trim();
    if (!content || isStreaming) return;

    const userMessage = newMessage("user", content);
    const assistantMessage = newMessage("assistant", "");
    const requestMessages: AgentMessage[] = [
      ...messages.map(({ role, content: messageContent }) => ({ role, content: messageContent })),
      { role: "user", content },
    ];

    if (messages.length === 0) setConversationTitle(content.slice(0, 28));
    setMessages((current) => [...current, userMessage, assistantMessage]);
    setInput("");
    setIsStreaming(true);
    setStatus("Jev 正在判断处理方式…");
    const controller = new AbortController();
    requestRef.current = controller;

    requestAnimationFrame(resizeComposer);

    try {
      await streamAgentReply(
        requestMessages,
        {
          onEvent: (event) => {
            const nextStatus = statusForEvent(event);
            if (nextStatus) setStatus(nextStatus);
            if (event.type === "delta" && event.content) {
              updateAssistant(assistantMessage.id, event.content);
            }
          },
        },
        controller.signal,
      );
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      const message = error instanceof Error ? error.message : "未知错误";
      updateAssistant(assistantMessage.id, `连接失败：${message}`, false);
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
      setIsStreaming(false);
      setStatus(IDLE_STATUS);
      requestAnimationFrame(() => textareaRef.current?.focus());
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    void submitMessage();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void submitMessage();
    }
  };

  const startNewChat = (): void => {
    setActiveView("chat");
    requestRef.current?.abort();
    requestRef.current = null;
    setMessages([]);
    setInput("");
    setConversationTitle("新对话");
    setStatus(IDLE_STATUS);
    setIsStreaming(false);
    requestAnimationFrame(() => {
      resizeComposer();
      textareaRef.current?.focus();
    });
  };

  return (
    <div className="window">
      <aside className="sidebar">
        <div className="traffic-lights" aria-hidden="true"><i /><i /><i /></div>
        <button className="new-chat" type="button" onClick={startNewChat}>
          <span className="new-chat__icon">＋</span>
          新建对话
          <span className="shortcut">⌘N</span>
        </button>
        <div className="sidebar__section">
          <span className="sidebar__label">工作台</span>
          <button
            className={`history-item${activeView === "chat" ? " history-item--active" : ""}`}
            type="button"
            onClick={() => setActiveView("chat")}
          >
            <span className="history-item__icon">◇</span>
            <span>对话</span>
          </button>
          <button
            className={`history-item${activeView === "notes" ? " history-item--active" : ""}`}
            type="button"
            onClick={() => setActiveView("notes")}
          >
            <span className="history-item__icon">▤</span>
            <span>笔记</span>
          </button>
        </div>
        <div className="sidebar__section">
          <span className="sidebar__label">今天</span>
          <button className="history-item" type="button" onClick={() => setActiveView("chat")}>
            <span className="history-item__icon">◇</span>
            <span>{conversationTitle}</span>
          </button>
        </div>
        <div className="sidebar__footer">
          <span className="status-dot" />
          本地服务
          <span className="platform">Personal Agent</span>
        </div>
      </aside>

      {activeView === "notes" ? <NotesPage /> : <main className="chat">
        <header className="chat__header">
          <div>
            <strong>Personal Work Agent</strong>
            <span className="model-status" data-active={isStreaming}>{status}</span>
          </div>
          <button className="header-action" type="button" title="更多选项">•••</button>
        </header>

        <section className="chat__content">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="agent-mark">✦</div>
              <h1>今天想处理什么？</h1>
              <p>与 DeepSeek 对话，整理想法、分析问题或推进你的工作。</p>
              <div className="suggestions">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion.label}
                    type="button"
                    onClick={() => {
                      setInput(suggestion.prompt);
                      requestAnimationFrame(() => {
                        resizeComposer();
                        textareaRef.current?.focus();
                      });
                    }}
                  >
                    {suggestion.label}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <div ref={messagesRef} className="messages" aria-live="polite">
            {messages.map((message) => (
              <article key={message.id} className={`message message--${message.role}`}>
                <div className="message__avatar">{message.role === "user" ? "你" : "✦"}</div>
                <div className="message__body">{message.content}</div>
              </article>
            ))}
          </div>
        </section>

        <footer className="composer-wrap">
          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              disabled={isStreaming}
              placeholder="发送消息给 Personal Work Agent"
              aria-label="聊天消息"
              autoFocus
              onChange={(event) => {
                setInput(event.target.value);
                requestAnimationFrame(resizeComposer);
              }}
              onKeyDown={handleKeyDown}
            />
            <div className="composer__actions">
              <button className="tool-button" type="button" title="添加上下文">＋</button>
              <span>Enter 发送 · Shift Enter 换行</span>
              <button className="send-button" type="submit" title="发送" disabled={isStreaming || !input.trim()}>
                ↑
              </button>
            </div>
          </form>
        </footer>
      </main>}
    </div>
  );
}
