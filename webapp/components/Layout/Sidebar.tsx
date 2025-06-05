'use client';
import { useContext } from 'react';
import { Mic, Image, FileText, Search, MessageSquare } from 'lucide-react';
import { ChatContext } from '../../context/ChatProvider';

const items = [
  { mode: 'text', icon: MessageSquare, label: 'Text' },
  { mode: 'voice', icon: Mic, label: 'Voice' },
  { mode: 'image', icon: Image, label: 'Image/PDF' },
  { mode: 'search', icon: Search, label: 'Search' }
] as const;

export default function Sidebar() {
  const { mode, setMode } = useContext(ChatContext);
  return (
    <aside className="hidden w-16 flex-col border-r py-4 md:flex">
      {items.map(({ mode: m, icon: Icon, label }) => (
        <button
          key={m}
          aria-label={label}
          onClick={() => setMode(m)}
          className={`flex flex-col items-center gap-1 p-2 hover:text-primary ${
            mode === m ? 'text-primary' : ''
          }`}
        >
          <Icon size={20} />
          <span className="text-xs">{label}</span>
        </button>
      ))}
    </aside>
  );
}
