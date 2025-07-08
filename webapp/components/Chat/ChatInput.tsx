'use client';
import { useContext, useState } from 'react';
import { Send, Mic, Image as ImgIcon, Search } from 'lucide-react';
import type { Blob } from 'buffer';
import { ChatContext } from '../../context/ChatProvider';
import { Button } from '../Shared/Button';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';
import { laionSearchImage } from '../../services/chatService';

export default function ChatInput() {
  const { mode, sendUserInput, setMode } = useContext(ChatContext);
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const { start, stop, isRecording } = useSpeechRecognition();

  // Add state for LAION results
  const [laionResults, setLaionResults] = useState<any[]>([]);

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

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getModeLabel = () => {
    switch (mode) {
      case 'text': return 'Text Chat';
      case 'voice': return 'Voice Input';
      case 'image': return 'Image Upload';
      case 'search': return 'Web Search';
      default: return 'Text Chat';
    }
  };

  // Handler for LAION image upload
  const handleLaionImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await laionSearchImage(file, 5);
      setLaionResults(res.results);
    } catch (err) {
      alert('LAION search failed');
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      {/* Mode indicator */}
      <div className="mb-2 text-sm text-gray-500 dark:text-gray-400 text-center">
        Mode: {getModeLabel()}
      </div>

      {mode === 'text' && (
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyPress={handleKeyPress}
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
            onKeyPress={handleKeyPress}
            placeholder="Search the web…"
          />
          <Button onClick={handleSend} aria-label="search">
            <Search size={20} />
          </Button>
        </div>
      )}

      {/* LAION image search upload */}
      <input type="file" accept="image/*" onChange={handleLaionImage} style={{ display: 'none' }} id="laion-upload" />
      <label htmlFor="laion-upload" style={{ cursor: 'pointer', marginLeft: 8 }}>
        <span role="img" aria-label="LAION">🔍🖼️</span>
      </label>

      {/* Show LAION results */}
      {laionResults.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h4>LAION Similar Images:</h4>
          <ul>
            {laionResults.map((r, i) => (
              <li key={i}>
                <a href={r.url} target="_blank" rel="noopener noreferrer">{r.caption}</a> (score: {r.score.toFixed(3)})
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-2 flex justify-around text-muted-foreground">
        <button 
          onClick={() => setMode('text')} 
          aria-label="text"
          className={`p-2 rounded ${mode === 'text' ? 'bg-blue-100 dark:bg-blue-900' : ''}`}
        >
          <Send size={16} />
        </button>
        <button 
          onClick={() => setMode('voice')} 
          aria-label="voice"
          className={`p-2 rounded ${mode === 'voice' ? 'bg-blue-100 dark:bg-blue-900' : ''}`}
        >
          <Mic size={16} />
        </button>
        <button 
          onClick={() => setMode('image')} 
          aria-label="image/pdf"
          className={`p-2 rounded ${mode === 'image' ? 'bg-blue-100 dark:bg-blue-900' : ''}`}
        >
          <ImgIcon size={16} />
        </button>
        <button 
          onClick={() => setMode('search')} 
          aria-label="search"
          className={`p-2 rounded ${mode === 'search' ? 'bg-blue-100 dark:bg-blue-900' : ''}`}
        >
          <Search size={16} />
        </button>
      </div>
    </div>
  );
}
