import { FormEvent, KeyboardEvent, useEffect, useLayoutEffect, useRef, useState } from "react";

import { streamConversationReply } from "./agent-api";
import {
  createConversation, listConversations, listMessages,
  type Conversation, type StoredMessage,
} from "./conversations-api";
import NotesPage from "./NotesPage";
import type { ChatMessage, StreamEvent } from "./types";

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

const fromStoredMessage = (message: StoredMessage): ChatMessage => ({
  id: String(message.id), role: message.role, content: message.content,
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
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [hasMoreConversations, setHasMoreConversations] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState(IDLE_STATUS);
  const messagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const requestRef = useRef<AbortController | null>(null);
  const selectionVersion = useRef(0);
  const skipNextLoad = useRef<number | null>(null);
  const preserveScroll = useRef<{ height: number; top: number } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const initialSelection = selectionVersion.current;
    listConversations(undefined, controller.signal).then((items) => {
      if (selectionVersion.current === initialSelection) {
        setConversations(items);
      } else {
        setConversations((current) => [...current, ...items.filter(
          (item) => !current.some((existing) => existing.id === item.id),
        )]);
      }
      setHasMoreConversations(items.length === 30);
      if (selectionVersion.current === initialSelection && items[0]) {
        setConversationId(items[0].id);
      }
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setHistoryError(error instanceof Error ? error.message : "加载会话失败");
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (conversationId === null) return;
    if (skipNextLoad.current === conversationId) {
      skipNextLoad.current = null;
      return;
    }
    const controller = new AbortController();
    setIsLoadingMessages(true);
    setHistoryError(null);
    setMessages([]);
    listMessages(conversationId, undefined, controller.signal).then((items) => {
      setMessages(items.map(fromStoredMessage));
      setHasMoreMessages(items.length === 50);
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setHistoryError(error instanceof Error ? error.message : "加载消息失败");
    }).finally(() => {
      if (!controller.signal.aborted) setIsLoadingMessages(false);
    });
    return () => controller.abort();
  }, [conversationId]);

  useLayoutEffect(() => {
    const element = messagesRef.current;
    if (!element) return;
    if (preserveScroll.current) {
      element.scrollTop = preserveScroll.current.top + element.scrollHeight - preserveScroll.current.height;
      preserveScroll.current = null;
    } else {
      element.scrollTop = element.scrollHeight;
    }
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
    if (!content || isStreaming || isLoadingMessages) return;
    if (conversationId === null) selectionVersion.current += 1;

    const userMessage = newMessage("user", content);
    const assistantMessage = newMessage("assistant", "");
    setMessages((current) => [...current, userMessage, assistantMessage]);
    setInput("");
    setIsStreaming(true);
    setStatus("Jev 正在判断处理方式…");
    const controller = new AbortController();
    requestRef.current = controller;
    const activeSelection = selectionVersion.current;

    requestAnimationFrame(resizeComposer);

    try {
      let activeId = conversationId;
      if (activeId === null) {
        const created = await createConversation(content.slice(0, 28));
        if (selectionVersion.current !== activeSelection) return;
        activeId = created.id;
        skipNextLoad.current = activeId;
        setConversationId(activeId);
        setConversations((current) => [created, ...current]);
      }
      await streamConversationReply(
        activeId,
        content,
        {
          onEvent: (event) => {
            if (selectionVersion.current !== activeSelection) return;
            const nextStatus = statusForEvent(event);
            if (nextStatus) setStatus(nextStatus);
            if (event.type === "delta" && event.content) {
              updateAssistant(assistantMessage.id, event.content);
            }
          },
        },
        controller.signal,
      );
      if (selectionVersion.current === activeSelection) {
        void listConversations().then((items) => {
          if (selectionVersion.current !== activeSelection) return;
          setConversations(items);
          setHasMoreConversations(items.length === 30);
        }).catch(() => undefined);
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      if (selectionVersion.current !== activeSelection) return;
      const message = error instanceof Error ? error.message : "未知错误";
      updateAssistant(assistantMessage.id, `发送失败：${message}`, false);
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
      if (selectionVersion.current === activeSelection) {
        setIsStreaming(false);
        setStatus(IDLE_STATUS);
        requestAnimationFrame(() => textareaRef.current?.focus());
      }
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
    selectionVersion.current += 1;
    preserveScroll.current = null;
    setActiveView("chat");
    requestRef.current?.abort();
    requestRef.current = null;
    setMessages([]);
    setConversationId(null);
    setHasMoreMessages(false);
    setIsLoadingMessages(false);
    setHistoryError(null);
    setInput("");
    setStatus(IDLE_STATUS);
    setIsStreaming(false);
    requestAnimationFrame(() => {
      resizeComposer();
      textareaRef.current?.focus();
    });
  };

  const selectConversation = (id: number): void => {
    if (conversationId === id) {
      setActiveView("chat");
      return;
    }
    selectionVersion.current += 1;
    preserveScroll.current = null;
    requestRef.current?.abort();
    requestRef.current = null;
    setIsStreaming(false);
    setActiveView("chat");
    setConversationId(id);
    setMessages([]);
    setHasMoreMessages(false);
    setIsLoadingMessages(false);
    setInput("");
    setStatus(IDLE_STATUS);
  };

  const loadOlderMessages = async (): Promise<void> => {
    if (conversationId === null || messages.length === 0 || isLoadingMessages) return;
    const activeSelection = selectionVersion.current;
    const firstId = Number(messages[0].id);
    if (!Number.isSafeInteger(firstId)) return;
    const element = messagesRef.current;
    if (element) preserveScroll.current = { height: element.scrollHeight, top: element.scrollTop };
    setIsLoadingMessages(true);
    try {
      const older = await listMessages(conversationId, firstId);
      if (selectionVersion.current !== activeSelection) {
        preserveScroll.current = null;
        return;
      }
      setMessages((current) => [...older.map(fromStoredMessage), ...current]);
      setHasMoreMessages(older.length === 50);
    } catch (error) {
      if (selectionVersion.current !== activeSelection) return;
      preserveScroll.current = null;
      setHistoryError(error instanceof Error ? error.message : "加载消息失败");
    } finally {
      if (selectionVersion.current === activeSelection) setIsLoadingMessages(false);
    }
  };

  const loadMoreConversations = async (): Promise<void> => {
    const lastId = conversations.at(-1)?.id;
    if (lastId === undefined) return;
    try {
      const older = await listConversations(lastId);
      setConversations((current) => [...current, ...older.filter(
        (item) => !current.some((existing) => existing.id === item.id),
      )]);
      setHasMoreConversations(older.length === 30);
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : "加载会话失败");
    }
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
        <div className="sidebar__section sidebar__section--history">
          <span className="sidebar__label">聊天记录</span>
          <div className="history-list">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                className={`history-item${activeView === "chat" && conversationId === conversation.id ? " history-item--active" : ""}`}
                type="button"
                onClick={() => selectConversation(conversation.id)}
              >
                <span className="history-item__icon">◇</span>
                <span>{conversation.title}</span>
              </button>
            ))}
            {hasMoreConversations && (
              <button className="history-more" type="button" onClick={() => void loadMoreConversations()}>加载更多会话</button>
            )}
          </div>
          {historyError && <p className="history-error" role="alert">{historyError}</p>}
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
          {messages.length === 0 && !isLoadingMessages ? (
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
            {hasMoreMessages && (
              <button className="load-older" type="button" disabled={isLoadingMessages} onClick={() => void loadOlderMessages()}>
                {isLoadingMessages ? "加载中…" : "加载更早消息"}
              </button>
            )}
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
              disabled={isStreaming || isLoadingMessages}
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
              <button className="send-button" type="submit" title="发送" disabled={isStreaming || isLoadingMessages || !input.trim()}>
                ↑
              </button>
            </div>
          </form>
        </footer>
      </main>}
    </div>
  );
}
