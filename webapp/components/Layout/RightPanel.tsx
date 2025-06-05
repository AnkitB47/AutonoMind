'use client';
import { useContext } from 'react';
import { ChatContext } from '../../context/ChatProvider';

export default function RightPanel() {
  const { clearMessages } = useContext(ChatContext);
  return (
    <aside className="hidden w-64 flex-col border-l p-4 md:flex">
      <button className="mb-4 text-sm underline" onClick={clearMessages}>
        Clear Chat
      </button>
      <div className="text-sm text-muted-foreground">Recent conversations...</div>
    </aside>
  );
}
