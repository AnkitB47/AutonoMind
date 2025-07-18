'use client';
import { createContext, useState, ReactNode, useEffect } from 'react';
import { sendMessage } from '../services/chatService';
import getApiBase from '../utils/getApiBase';

export type Mode = 'text' | 'voice' | 'image' | 'search';

type ImageResult = { imageUrl: string; score: number };

export interface Message {
  role: 'user' | 'bot';
  content: string;
  /** optional array of image results for image RAG */
  imageResults?: ImageResult[];
  /** optional description for image queries */
  description?: string;
  /** optional source tag for RAG / web fallback */
  source?: string | null;
  /** timestamp for display */
  ts: number;
  /** optional error flag for error messages */
  error?: boolean;
}

interface ChatCtx {
  mode: Mode;
  messages: Message[];
  loading: boolean;
  error: string | null;
  language: string;
  setLanguage: (l: string) => void;
  setMode: (m: Mode) => void;
  sessionId: string;
  sendUserInput: (value: string | File | Blob) => void;
  clearMessages: () => void;
}

export const ChatContext = createContext<ChatCtx>({} as ChatCtx);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>('text');
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === 'undefined') return [];
    const saved = localStorage.getItem('am_history');
    return saved ? JSON.parse(saved) : [];
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [language, setLanguage] = useState('en');
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window === 'undefined') return crypto.randomUUID();
    return localStorage.getItem('am_session') || crypto.randomUUID();
  });
  // Track the last uploaded file type to preserve context
  const [lastUploadType, setLastUploadType] = useState<'pdf' | 'image' | null>(null);

  useEffect(() => {
    // Test API connectivity on mount
    fetch('/api/debug-env')
      .then(r => r.json())
      .then(data => console.debug('API connectivity test:', data))
      .catch(e => console.error('API connectivity test failed:', e));
  }, []);

  useEffect(() => {
    localStorage.setItem('am_history', JSON.stringify(messages));
    localStorage.setItem('am_session', sessionId);
  }, [messages, sessionId]);

  // Helper function to detect if a query should be treated as an image query
  const shouldTreatAsImageQuery = (query: string): boolean => {
    if (lastUploadType !== 'image') return false;
    
    const imageKeywords = [
      'image', 'picture', 'photo', 'photo', 'look', 'see', 'show', 'display',
      'what is this', 'what does this look like', 'describe this', 'similar',
      'appears', 'contains', 'shows', 'depicts', 'represents', 'illustrates'
    ];
    
    const lowerQuery = query.toLowerCase();
    return imageKeywords.some(keyword => lowerQuery.includes(keyword));
  };

  const sendUserInput = async (input: string|File|Blob) => {
    const isFile = input instanceof File;
    const userText = isFile ? '[file]' : input;
    setMessages(m => [...m, { role:'user', content:String(userText), ts:Date.now() }]);
    setLoading(true);
    setError(null);

    try {
      if (isFile) {
        // file branch - upload to /upload or /image-analyze endpoint
        const fileName = (input as File).name.toLowerCase();
        const data = await sendMessage(sessionId, mode, language, input);
        if (data.error) {
          setMessages(m => [...m, { role: 'bot', content: data.error, ts: Date.now(), error: true }]);
          setError(data.error);
          setLoading(false);
          return;
        }
        if (fileName.endsWith('.pdf')) {
          if (data.session_id) setSessionId(data.session_id);
          setMessages(m => [...m, { role:'bot', content:data.message, ts:Date.now() }]);
          setLastUploadType('pdf');
          setMode('text');
        } else if (fileName.match(/\.(png|jpg|jpeg|gif|webp)$/)) {
          // Handle new image RAG response
          if (data.session_id) setSessionId(data.session_id);
          let content = '';
          if (data.caption) {
            content += `Your uploaded image depicts:\n'${data.caption}'\n`;
          }
          if (data.clip_message) {
            content += `\n${data.clip_message}`;
          }
          setMessages(m => [...m, {
            role: 'bot',
            content,
            imageResults: data.similar_images?.map((img: any) => ({
              imageUrl: img.url,
              score: img.score
            })),
            description: data.caption,
            ts: Date.now()
          }]);
          setLastUploadType('image');
          setMode('image');
        } else {
          // fallback for other file types
          setMessages(m => [...m, { role:'bot', content:data.message, ts:Date.now() }]);
        }
        return;
      }
      // chat branch (streams) - use /chat endpoint
      // Always use 'text' mode for text queries, even if last upload was image
      const res = await sendMessage(sessionId, 'text', language, input as string);
      if (!res.body) return setLoading(false);
      const source = res.headers.get('X-Source');
      const sessionIdHeader = res.headers.get('X-Session-ID');
      if (sessionIdHeader) setSessionId(sessionIdHeader);
      
      // Check if response is JSON (image query result or error)
      const contentType = res.headers.get('Content-Type');
      if (contentType && contentType.includes('application/json')) {
        const responseData = await res.json();
        if (responseData.error) {
          setMessages(m => [...m, { role: 'bot', content: responseData.error, ts: Date.now(), error: true }]);
          setError(responseData.error);
          setLoading(false);
          return;
        }
        // Handle top-N image results
        if (responseData.results && Array.isArray(responseData.results)) {
          setMessages(m => [...m, {
            role: 'bot',
            content: '',
            imageResults: responseData.results.map((r: any) => ({
              imageUrl: r.image_url,
              score: r.score
            })),
            description: responseData.description,
            source,
            ts: Date.now()
          }]);
        } else {
          setMessages(m => [...m, {
            role: 'bot',
            content: '',
            description: responseData.description,
            source,
            ts: Date.now()
          }]);
        }
      } else {
        // Handle streaming text response
        setMessages(m => [...m, { role: 'bot', content: '', source, ts: Date.now() }]);
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let done = false;
        while (!done) {
          const { value, done: d } = await reader.read();
          done = d;
          const chunk = dec.decode(value || new Uint8Array());
          setMessages(msgs => {
            const copy = [...msgs];
            copy[copy.length-1].content += chunk;
            return copy;
          });
        }
      }
    } catch (e: any) {
      console.error('Error in sendUserInput:', e);
      setMessages(m => [...m, { role: 'bot', content: e.message || 'An error occurred', ts: Date.now(), error: true }]);
      setError(e.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    setLastUploadType(null);
    localStorage.removeItem('am_history');
  };

  return (
    <ChatContext.Provider
      value={{
        mode, messages, loading, error, language,
        setLanguage, setMode, sessionId, sendUserInput, clearMessages
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}
