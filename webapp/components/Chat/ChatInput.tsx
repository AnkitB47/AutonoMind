'use client';
import { useContext, useState } from 'react';
import { Send, Mic, Image, FileText, Search } from 'lucide-react';
import { ChatContext } from '../../context/ChatProvider';
import { Button } from '../Shared/Button';

export default function ChatInput() {
  const { mode, sendMessage, setMode, uploadFile } = useContext(ChatContext);
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const handleSend = () => {
    if (mode === 'text' && text.trim()) {
      sendMessage(text);
      setText('');
    } else if (mode === 'image' && file) {
      uploadFile(file);
      setFile(null);
    }
  };

  return (
    <div className="border-t bg-background p-4">
      {mode === 'text' && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your message..."
          />
          <Button aria-label="send" onClick={handleSend}>
            <Send size={20} />
          </Button>
        </div>
      )}
      {mode === 'voice' && (
        <div className="flex justify-center">
          <Button aria-label="record" onClick={() => sendMessage('[voice]')}
            className="h-12 w-12 rounded-full border">
            <Mic />
          </Button>
        </div>
      )}
      {mode === 'image' && (
        <div className="flex flex-col items-center gap-2">
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <Button onClick={handleSend}>Upload</Button>
        </div>
      )}
      {mode === 'search' && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Search the web..."
          />
          <Button aria-label="search" onClick={handleSend}>
            <Search size={20} />
          </Button>
        </div>
      )}
      <div className="mt-2 flex justify-around text-muted-foreground">
        <button aria-label="text" onClick={() => setMode('text')}>
          <Send size={16} />
        </button>
        <button aria-label="voice" onClick={() => setMode('voice')}>
          <Mic size={16} />
        </button>
        <button aria-label="image" onClick={() => setMode('image')}>
          <Image size={16} />
        </button>
        <button aria-label="search" onClick={() => setMode('search')}>
          <Search size={16} />
        </button>
      </div>
    </div>
  );
}
