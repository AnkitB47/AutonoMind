'use client';
import { createContext, useContext, useState, ReactNode } from 'react';
import { sendTextMessage, uploadFile as uploadFileSvc } from '../services/chatService';

export type Mode = 'text' | 'voice' | 'image' | 'search';

export interface Message {
  role: 'user' | 'bot';
  content: string;
}

interface ChatCtx {
  mode: Mode;
  messages: Message[];
  setMode: (m: Mode) => void;
  sendMessage: (text: string) => void;
  uploadFile: (file: File) => void;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatCtx>({} as ChatCtx);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>('text');
  const [messages, setMessages] = useState<Message[]>([]);

  const sendMessage = (text: string) => {
    setMessages((m) => [...m, { role: 'user', content: text }]);
    sendTextMessage(text).then((res) =>
      setMessages((m) => [...m, { role: 'bot', content: res }])
    );
  };

  const uploadFile = (file: File) => {
    setMessages((m) => [...m, { role: 'user', content: file.name }]);
    uploadFileSvc(file).then((res) =>
      setMessages((m) => [...m, { role: 'bot', content: res }])
    );
  };

  const clearMessages = () => setMessages([]);

  return (
    <ChatContext.Provider
      value={{ mode, messages, setMode, sendMessage, uploadFile, clearMessages }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export { ChatContext };
