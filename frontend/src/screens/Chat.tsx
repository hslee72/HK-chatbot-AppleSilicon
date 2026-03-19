import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CitationBubble from '../components/CitationBubble';
import type { ChatMessage, Tenant, ChatResponse } from '../types/api';

export default function ChatScreen() {
  const navigate = useNavigate();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState('default');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const isComposing = useRef(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetch('/api/tenants')
      .then((r) => r.json())
      .then(setTenants)
      .catch(console.error);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = { role: 'user', content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput('');
    setSending(true);

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          question: text,
          history: next.slice(-6).map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      const data: ChatResponse = await resp.json();

      if (!resp.ok) {
        throw new Error((data as unknown as { detail: string }).detail || 'Server error');
      }

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
      };
      setMessages([...next, assistantMsg]);
    } catch (e) {
      setMessages([
        ...next,
        { role: 'assistant', content: `오류: ${(e as Error).message}` },
      ]);
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing.current) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex flex-col bg-gray-900 text-white shrink-0">
        <div className="px-4 py-4">
          <h1 className="text-base font-bold tracking-tight">HK Chatbot</h1>
          <p className="text-[10px] text-gray-400 mt-0.5">규정 RAG 챗봇</p>
        </div>

        {/* Tenant selector */}
        <div className="px-3 pb-3">
          <label className="text-[10px] text-gray-500 uppercase tracking-wide block mb-1">
            테넌트
          </label>
          <select
            value={tenantId}
            onChange={(e) => {
              setTenantId(e.target.value);
              setMessages([]);
            }}
            className="w-full bg-gray-800 text-xs text-white border border-gray-700 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1" />

        {/* Nav */}
        <div className="p-3 border-t border-gray-700 space-y-1">
          <button
            onClick={() => setMessages([])}
            className="w-full text-left px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            + 새 대화
          </button>
          <button
            onClick={() => navigate('/documents')}
            className="w-full text-left px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            📄 문서 관리
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shrink-0">
          <span className="text-sm font-medium text-gray-700">
            {tenants.find((t) => t.id === tenantId)?.name ?? '규정 RAG 챗봇'}
          </span>
        </header>

        {/* Messages */}
        <main className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400">
              <div className="text-4xl mb-3">📋</div>
              <p className="text-sm">규정에 대해 질문하세요</p>
              <p className="text-xs mt-1 text-gray-300">
                문서가 인덱싱되어 있어야 합니다
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-sm'
                    : 'bg-white text-gray-800 shadow-sm rounded-bl-sm'
                }`}
              >
                {msg.role === 'assistant' && msg.citations ? (
                  <CitationBubble
                    content={msg.content}
                    citations={msg.citations}
                  />
                ) : (
                  <div className="whitespace-pre-wrap break-words text-sm">
                    {msg.content}
                  </div>
                )}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center">
                  <span className="typing-dot" style={{ animationDelay: '0ms' }} />
                  <span className="typing-dot" style={{ animationDelay: '200ms' }} />
                  <span className="typing-dot" style={{ animationDelay: '400ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </main>

        {/* Input */}
        <footer className="px-4 py-3 bg-white border-t border-gray-200">
          <div className="flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onCompositionStart={() => { isComposing.current = true; }}
              onCompositionEnd={() => { isComposing.current = false; }}
              onKeyDown={handleKeyDown}
              placeholder="규정에 대해 질문하세요… (Enter 전송, Shift+Enter 줄바꿈)"
              rows={1}
              className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all max-h-32 overflow-y-auto"
              style={{ lineHeight: '1.5' }}
              onInput={(e) => {
                const el = e.currentTarget;
                el.style.height = 'auto';
                el.style.height = Math.min(el.scrollHeight, 128) + 'px';
              }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || sending}
              className="px-4 py-2.5 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
            >
              전송
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
