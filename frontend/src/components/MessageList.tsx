import React from 'react'

export interface ChatMessage {
  sender: 'user' | 'bot'
  text: string
}

interface Props {
  messages: ChatMessage[]
}

export const MessageList: React.FC<Props> = ({ messages }) => (
  <div className="space-y-2">
    {messages.map((m, idx) => (
      <div
        key={idx}
        className={`p-2 rounded ${m.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-700'}`}
      >
        {m.text}
      </div>
    ))}
  </div>
)
