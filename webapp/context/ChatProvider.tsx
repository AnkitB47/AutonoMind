// webapp/context/ChatProvider.tsx
'use client';
import { createContext, useState, ReactNode, useEffect } from 'react';
import getApiBase from '../utils/getApiBase';

export type Mode = 'text'|'voice'|'image'|'search';

export interface Message { role:'user'|'bot'; content:string; source?:string|null; ts:number; }

interface Ctx { mode:Mode; messages:Message[]; loading:boolean; error:string|null;
  language:string; setLanguage:(l:string)=>void; setMode:(m:Mode)=>void;
  sessionId:string; setSessionId:(id:string)=>void; sendUserInput:(v:string|File)=>void; clearMessages():void;
}

export const ChatContext = createContext<Ctx>({} as Ctx);

export function ChatProvider({children}:{children:ReactNode}){
  const [mode,setMode]=useState<Mode>('text');
  const [messages,setMessages]=useState<Message[]>(()=>
    typeof window==='undefined'?[]:JSON.parse(localStorage.getItem('am_history')||'[]'));
  const [loading,setLoading]=useState(false), [error,setError]=useState<string|null>(null);
  const [language,setLanguage]=useState('en');
  const [sessionId,setSessionId]=useState(()=>
    typeof window==='undefined'?crypto.randomUUID():localStorage.getItem('am_session')||crypto.randomUUID());

  useEffect(()=>{
    localStorage.setItem('am_history',JSON.stringify(messages));
    localStorage.setItem('am_session',sessionId);
  },[messages,sessionId]);

  const blobToBase64=(b:Blob)=>new Promise<string>(res=>{
    const r=new FileReader();
    r.onloadend=()=>res((r.result as string).split(',')[1]);
    r.readAsDataURL(b);
  });

  const sendUserInput=async(input:string|File)=>{
    setMessages(m=>[...m,{role:'user',content:typeof input==='string'?input:'[file]',ts:Date.now()}]);
    setLoading(true); setError(null);

    // any File → upload
    if(input instanceof File){
      const form=new FormData(); form.append('file',input); form.append('session_id',sessionId);
      const up=await fetch(`${getApiBase()}/upload`,{method:'POST',body:form});
      const data=await up.json(); if(data.session_id) setSessionId(data.session_id);
      setMessages(m=>[...m,{role:'bot',content:data.message,ts:Date.now()}]);
      setLoading(false); return;
    }

    // else → chat stream
    const payload=typeof input==='string'?input:await blobToBase64(input);
    const res=await fetch(`${getApiBase()}/chat`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({session_id:sessionId,mode,lang:language,content:payload})
    });
    if(!res.body){ setLoading(false); return; }
    const src=res.headers.get('x-source');
    setMessages(m=>[...m,{role:'bot',content:'',source:src,ts:Date.now()}]);
    const reader=res.body.getReader(),dec=new TextDecoder();
    let done=false;
    while(!done){
      const {value,done:d}=await reader.read(); done=d;
      const chunk=dec.decode(value||new Uint8Array());
      setMessages(msgs=>{
        const cp=[...msgs];
        cp[cp.length-1].content+=chunk;
        return cp;
      });
    }
    setLoading(false);
  };

  const clearMessages=()=>{ setMessages([]); localStorage.removeItem('am_history'); };

  return <ChatContext.Provider value={{
    mode,messages,loading,error,language,
    setLanguage,setMode,sessionId,setSessionId,
    sendUserInput,clearMessages
  }}>{children}</ChatContext.Provider>;
}
