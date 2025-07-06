'use client';
import { createContext, useState, ReactNode, useEffect } from 'react';
import { sendMessage } from '../services/chatService';
import getApiBase from '../utils/getApiBase';

export type Mode = 'text' | 'voice' | 'image' | 'search';

export interface Message {
  role: 'user' | 'bot';
  content: string;
  /** optional URL of an ingested image (RAG result) */
  imageUrl?: string;
  /** optional source tag for RAG / web fallback */
  source?: string | null;
  /** timestamp for display */
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
  sendUserInput: (value: string | File | Blob) => void;
  clearMessages: () => void;
}

export const ChatContext = createContext<ChatCtx>({} as ChatCtx);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>('text');
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === 'undefined') return [];
    const saved = localStorage.getItem('am_history');
    return saved ? JSON.parse(saved) : [];
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [language, setLanguage] = useState('en');
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window === 'undefined') return crypto.randomUUID();
    return localStorage.getItem('am_session') || crypto.randomUUID();
  });

  useEffect(() => {
    fetch('/api/debug-env')
      .then(r => r.json())
      .then(data => console.debug('debug-env', data))
      .catch(e => console.error('debug-env', e));
  }, []);

  useEffect(() => {
    localStorage.setItem('am_history', JSON.stringify(messages));
    localStorage.setItem('am_session', sessionId);
  }, [messages, sessionId]);

  const sendUserInput = async (input: string|File|Blob) => {
    const isFile = input instanceof File;
    const userText = isFile ? '[file]' : input;
    setMessages(m => [...m, { role:'user', content:String(userText), ts:Date.now() }]);
    setLoading(true);
    setError(null);

    try {
      if (isFile) {
        // file branch - upload to /upload endpoint
        const url = `${getApiBase()}/upload`;
        console.debug('Uploading to', url);
        const form = new FormData();
        form.append('file', input as File);
        form.append('session_id', sessionId);
        const res = await fetch(url, { method: 'POST', body: form });
        const data = await res.json();
        if (data.session_id) setSessionId(data.session_id);
        setMessages(m => [...m, { role:'bot', content:data.message, ts:Date.now() }]);
        setMode('text');
      } else {
        // chat branch (streams) - use /chat endpoint
        const res = await sendMessage(sessionId, mode, language, input as string);
        if (!res.body) return setLoading(false);
        const source = res.headers.get('X-Source');
        const sessionIdHeader = res.headers.get('X-Session-ID');
        if (sessionIdHeader) setSessionId(sessionIdHeader);
        setMessages(m => [...m, { role:'bot', content:'', source, ts:Date.now() }]);
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let done = false;
        while (!done) {
          const { value, done: d } = await reader.read();
          done = d;
          const chunk = dec.decode(value || new Uint8Array());
          setMessages(msgs => {
            const copy = [...msgs];
            copy[copy.length-1].content += chunk;
            return copy;
          });
        }
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    localStorage.removeItem('am_history');
  };

  return (
    <ChatContext.Provider
      value={{
        mode, messages, loading, error, language,
        setLanguage, setMode, sessionId, sendUserInput, clearMessages
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}
