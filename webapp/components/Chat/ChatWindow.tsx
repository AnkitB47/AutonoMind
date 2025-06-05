'use client';
import { useContext, useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';
import ChatInput from './ChatInput';
import { ChatContext } from '../../context/ChatProvider';

export default function ChatWindow() {
  const { messages } = useContext(ChatContext);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m, idx) => (
          <ChatBubble key={idx} isUser={m.role === 'user'}>
            {m.content}
          </ChatBubble>
        ))}
        <div ref={bottomRef} />
      </div>
      <ChatInput />
    </div>
  );
}
