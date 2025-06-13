'use client';
import { createContext, useState, ReactNode } from 'react';
import { sendChat, uploadFile as uploadFileSvc } from '../services/chatService';

export type Mode = 'text' | 'voice' | 'image' | 'search';

export interface Message {
  role: 'user' | 'bot';
  content: string;
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

const ChatContext = createContext<ChatCtx>({} as ChatCtx);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>('text');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState('en');
  const [sessionId] = useState(() => crypto.randomUUID());

  const sendUserInput = async (input: string | File | Blob) => {
    setMessages((m) => [
      ...m,
      { role: 'user', content: typeof input === 'string' ? input : '[file]' },
    ]);
    setLoading(true);
    setError(null);
    try {
      const reply = await sendChat(input as any, mode, language, { sessionId });
      setMessages((m) => [...m, { role: 'bot', content: reply }]);
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
        sendUserInput,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export { ChatContext };
