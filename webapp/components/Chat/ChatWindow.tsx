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
          <ChatBubble key={i} isUser={m.role==='user'} source={m.source} error={m.error}>
            {m.imageResults && m.imageResults.length > 0 ? (
              <div className="space-y-2">
                <div className="flex flex-row space-x-4 overflow-x-auto pb-2">
                  {m.imageResults.map((img, idx) => (
                    <div key={idx} className="flex flex-col items-center">
                      <img
                        src={`${getApiBase()}${img.imageUrl}`}
                        alt={`RAG result ${idx+1}`}
                        className="max-w-xs max-h-48 rounded shadow-md border"
                      />
                      <div className="text-xs text-gray-500 mt-1">Score: {img.score.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
                {m.description && (
                  <div className="text-sm text-gray-600 dark:text-gray-300">
                    {m.description}
                  </div>
                )}
              </div>
            ) : (
              <div>
                {m.content}
                {m.description && (
                  <div className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                    {m.description}
                  </div>
                )}
              </div>
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
