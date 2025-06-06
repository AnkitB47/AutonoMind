'use client';
import { createContext, useContext, useState, ReactNode } from 'react';
import {
  sendTextMessage,
  uploadFile as uploadFileSvc,
  sendVoice as sendVoiceSvc,
} from '../services/chatService';

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
  sendMessage: (text: string) => void;
  sendVoice: (blob: Blob) => void;
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

  const sendMessage = async (text: string) => {
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setLoading(true);
    setError(null);
    try {
      const res = await sendTextMessage(text, language);
      setMessages((m) => [...m, { role: 'bot', content: res }]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const sendVoice = async (blob: Blob) => {
    setMessages((m) => [...m, { role: 'user', content: '[voice]' }]);
    setLoading(true);
    setError(null);
    try {
      const res = await sendVoiceSvc(blob, language);
      setMessages((m) => [...m, { role: 'bot', content: res }]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (file: File) => {
    setMessages((m) => [...m, { role: 'user', content: file.name }]);
    setLoading(true);
    setError(null);
    try {
      const res = await uploadFileSvc(file, language);
      setMessages((m) => [...m, { role: 'bot', content: res }]);
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
        sendMessage,
        sendVoice,
        uploadFile,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export { ChatContext };
