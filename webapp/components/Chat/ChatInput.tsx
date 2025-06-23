'use client';
import { useContext, useState } from 'react';
import { Send, Mic, Image, Search } from 'lucide-react';
import { ChatContext } from '../../context/ChatProvider';
import { Button } from '../Shared/Button';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';

export default function ChatInput() {
  const { mode, sendUserInput, uploadFile, setMode } = useContext(ChatContext);
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const { start, stop, isRecording } = useSpeechRecognition();

  const handleSend = () => {
    if (mode === 'image' && file) {
      uploadFile(file);
      setFile(null);
      return;
    }
    if (text.trim()) {
      sendUserInput(text);
      setText('');
    }
  };

  const handleRecord = async () => {
    if (isRecording) {
      const audio = await stop();
      if (audio) sendUserInput(audio);
    } else {
      start();
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      {mode === 'text' && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
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
          <Button
            aria-label="record"
            onClick={handleRecord}
            className={`relative h-12 w-12 rounded-full border ${isRecording ? 'animate-pulse ring-2 ring-primary' : ''}`}
          >
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
            className="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2"
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
