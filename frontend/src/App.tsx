import React, { useState } from 'react'
import api from './api'
import ChatInput from './components/ChatInput'
import { MessageList, ChatMessage } from './components/MessageList'

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const send = async (type: 'text' | 'voice' | 'image', data: FormData) => {
    const url = `/input/${type}`
    const res = await api.post(url, data)
    const content = type === 'text' ? data.get('query') as string : `[${type} uploaded]`
    setMessages(msgs => [...msgs, { sender: 'user', text: content }, { sender: 'bot', text: res.data.response }])
  }

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <h1 className="text-center text-2xl font-bold">🤖 AutonoMind Assistant</h1>
      <MessageList messages={messages} />
      <ChatInput onSend={send} />
    </div>
  )
}

export default App
