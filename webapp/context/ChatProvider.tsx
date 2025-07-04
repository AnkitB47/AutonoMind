'use client';
import { createContext, useState, ReactNode, useEffect } from 'react';
import getApiBase from '../utils/getApiBase';

export type Mode = 'text' | 'voice' | 'image' | 'search';

export interface Message {
  role: 'user' | 'bot';
  content: string;
  imageUrl?: string;
  source?: string | null;
  ts: number;
}

interface ChatCtx {
  mode: Mode;
  messages: Message[];
  loading: boolean;
  error: string | null;
  language: string;
  setLanguage: (l: string) => void;
  setMode: (m: Mode) => void;
  sessionId: string;
  setSessionId: (id: string) => void;
  sendUserInput: (value: string | File | Blob) => void;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatCtx>({} as ChatCtx);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>('text');
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const saved = localStorage.getItem('am_history');
      return saved ? (JSON.parse(saved) as Message[]) : [];
    } catch {
      return [];
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState('en');
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window === 'undefined') return crypto.randomUUID();
    const saved = localStorage.getItem('am_session');
    return saved || crypto.randomUUID();
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('am_history', JSON.stringify(messages));
      localStorage.setItem('am_session', sessionId);
    }
  }, [messages, sessionId]);

    const sendUserInput = async (input: string | Blob | File) => {
    const userText = typeof input === 'string' ? input : '[file]';
    setMessages((m) => [...m, { role: 'user', content: userText, ts: Date.now() }]);
    setLoading(true);
    setError(null);

    // Unified file-upload branch for images *or* PDFs
    if (
      input instanceof File &&
      (input.type.startsWith('image/') || input.type === 'application/pdf')
    ) {
      const form = new FormData();
      form.append('file', input);
      form.append('session_id', sessionId);
      const resUpload = await fetch(`${getApiBase()}/upload`, {
        method: 'POST',
        body: form,
      });
      const data = await resUpload.json();
      if (data.session_id) setSessionId(data.session_id);
      setMessages((m) => [
        ...m,
        { role: 'bot', content: data.message, ts: Date.now() },
      ]);
      setLoading(false);
      return;
    }

    const res = await fetch(`${getApiBase()}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        mode,
        lang: language,
        content: typeof input === 'string' ? input : await blobToBase64(input),
      }),
    });

    if (!res.body) {
      setLoading(false);
      return;
    }

    const source = res.headers.get('x-source');
    setMessages((m) => [...m, { role: 'bot', content: '', source, ts: Date.now() }]);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    while (!done) {
      const { value, done: d } = await reader.read();
      done = d;
      const chunk = decoder.decode(value || new Uint8Array());
      setMessages((msgs) => {
        const updated = [...msgs];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: updated[updated.length - 1].content + chunk,
        };
        return updated;
      });
    }
    setLoading(false);
  };

  function blobToBase64(b: Blob): Promise<string> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
      reader.readAsDataURL(b);
    });
  }
  const clearMessages = () => {
    setMessages([]);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('am_history');
    }
  };

  return (
    <ChatContext.Provider
      value={{
        mode,
        messages,
        loading,
        error,
        language,
        setLanguage,
        setMode,
        sessionId,
        setSessionId,
        sendUserInput,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export { ChatContext };
