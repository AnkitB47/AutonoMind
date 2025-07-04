'use client';
import { useContext, useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';
import ChatInput from './ChatInput';
import LoaderDots from '../Shared/LoaderDots';
import { ChatContext } from '../../context/ChatProvider';
import getApiBase from '../../utils/getApiBase';

export default function ChatWindow() {
  const { messages, loading, error } = useContext(ChatContext);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior:'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <ChatBubble key={i} isUser={m.role==='user'} source={m.source}>
            {m.imageUrl ? (
              <img
                src={`${getApiBase()}${m.imageUrl}`}
                alt="RAG result"
                className="max-w-xs rounded"
              />
            ) : (
              m.content
            )}
            <div className="text-xs opacity-50 mt-1">{new Date(m.ts).toLocaleTimeString()}</div>
          </ChatBubble>
        ))}
        {loading && (
          <ChatBubble>
            <span className="mr-2">Thinking…</span><LoaderDots/>
          </ChatBubble>
        )}
        {error && (
          <ChatBubble>
            <span className="text-destructive">{error}</span>
          </ChatBubble>
        )}
        <div ref={bottomRef}/>
      </div>
      <ChatInput/>
    </div>
  );
}
