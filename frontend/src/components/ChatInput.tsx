import React, { useRef, useState } from 'react'
import { FiSend, FiMic, FiImage } from 'react-icons/fi'

interface Props {
  onSend: (type: 'text' | 'voice' | 'image', data: FormData) => void
}

const ChatInput: React.FC<Props> = ({ onSend }) => {
  const [text, setText] = useState('')
  const voiceRef = useRef<HTMLInputElement>(null)
  const imageRef = useRef<HTMLInputElement>(null)

  const sendText = () => {
    if (!text) return
    const data = new FormData()
    data.append('query', text)
    onSend('text', data)
    setText('')
  }

  const sendFile = (type: 'voice' | 'image', ref: React.RefObject<HTMLInputElement>) => {
    const file = ref.current?.files?.[0]
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    onSend(type, data)
    ref.current!.value = ''
  }

  return (
    <div className="flex items-center space-x-2">
      <input
        className="flex-1 rounded border border-gray-600 bg-gray-800 p-2"
        placeholder="Ask something..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') sendText() }}
      />
      <button className="p-2" onClick={sendText} title="Send text">
        <FiSend />
      </button>
      <input type="file" accept="audio/*" ref={voiceRef} hidden onChange={() => sendFile('voice', voiceRef)} />
      <button className="p-2" onClick={() => voiceRef.current?.click()} title="Send voice">
        <FiMic />
      </button>
      <input type="file" accept="image/*" ref={imageRef} hidden onChange={() => sendFile('image', imageRef)} />
      <button className="p-2" onClick={() => imageRef.current?.click()} title="Send image">
        <FiImage />
      </button>
    </div>
  )
}

export default ChatInput
