'use client';
import { useContext, useState } from 'react';
import { Send, Mic, Image as ImgIcon, Search } from 'lucide-react';
import type { Blob } from 'buffer';
import { ChatContext } from '../../context/ChatProvider';
import { Button } from '../Shared/Button';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';

export default function ChatInput() {
  const { mode, sendUserInput, setMode } = useContext(ChatContext);
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const { start, stop, isRecording } = useSpeechRecognition();

  const handleSend = () => {
    // If an image or PDF is selected, upload it
    if (mode === 'image' && file) {
      sendUserInput(file);
      setFile(null);
      return;
    }

    // Otherwise, send text (including after voice transcription)
    if (text.trim()) {
      sendUserInput(text);
      setText('');
    }
  };

  const handleRecord = async () => {
    if (isRecording) {
      const audioBlob = await stop();
      if (audioBlob) {
        const file = new File(
          [audioBlob],
          `recording-${Date.now()}.webm`,
          { type: audioBlob.type }
        );
        sendUserInput(file);
      }
    } else {
      start();
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      {mode === 'text' && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Type your message…"
          />
          <Button onClick={handleSend} aria-label="send">
            <Send size={20} />
          </Button>
        </div>
      )}

      {mode === 'voice' && (
        <div className="flex justify-center">
          <Button
            onClick={handleRecord}
            aria-label="record"
            className={`h-12 w-12 rounded-full border ${
              isRecording ? 'animate-pulse ring-2 ring-primary' : ''
            }`}
          >
            <Mic />
          </Button>
        </div>
      )}

      {mode === 'image' && (
        <div className="flex flex-col items-center gap-2">
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={e => setFile(e.target.files?.[0] || null)}
          />
          <Button onClick={handleSend}>Upload</Button>
        </div>
      )}

      {mode === 'search' && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Search the web…"
          />
          <Button onClick={handleSend} aria-label="search">
            <Search size={20} />
          </Button>
        </div>
      )}

      <div className="mt-2 flex justify-around text-muted-foreground">
        <button onClick={() => setMode('text')} aria-label="text">
          <Send size={16} />
        </button>
        <button onClick={() => setMode('voice')} aria-label="voice">
          <Mic size={16} />
        </button>
        <button onClick={() => setMode('image')} aria-label="image/pdf">
          <ImgIcon size={16} />
        </button>
        <button onClick={() => setMode('search')} aria-label="search">
          <Search size={16} />
        </button>
      </div>
    </div>
  );
}
