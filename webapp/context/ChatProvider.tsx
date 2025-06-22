'use client';
import { createContext, useState, ReactNode } from 'react';
import { sendChat, uploadFile as uploadFileSvc } from '../services/chatService';

export type Mode = 'text' | 'voice' | 'image' | 'search';

export interface Message {
  role: 'user' | 'bot';
  content: string;
  imageUrl?: string;
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
  uploadFile: (file: File) => void;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatCtx>({} as ChatCtx);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>('text');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState('en');
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());

  const sendUserInput = async (input: string | File | Blob) => {
    setMessages((m) => [
      ...m,
      { role: 'user', content: typeof input === 'string' ? input : '[file]' },
    ]);
    setLoading(true);
    setError(null);
    try {
      const res = await sendChat(input as any, mode, language, { sessionId });
      if (res.session_id) setSessionId(res.session_id);
      if ('image_url' in res && res.image_url) {
        setMessages((m) => [...m, { role: 'bot', content: '', imageUrl: res.image_url }]);
      } else {
        const text = 'reply' in res ? res.reply : String(res);
        setMessages((m) => [...m, { role: 'bot', content: text }]);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (file: File) => {
    setMessages((m) => [...m, { role: 'user', content: '[file]' }]);
    setLoading(true);
    setError(null);
    try {
      const res = await uploadFileSvc(file, language, { sessionId });
      if (res.session_id) setSessionId(res.session_id);
      setMessages((m) => [...m, { role: 'bot', content: res.message }]);
      setMode('text');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const clearMessages = () => setMessages([]);

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
        uploadFile,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export { ChatContext };
