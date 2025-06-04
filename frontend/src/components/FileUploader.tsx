import React, { useRef, useState } from 'react'
import { FiUpload } from 'react-icons/fi'
import api from '../api'

interface Props {
  onSuccess?: (msg: string) => void
}

const FileUploader: React.FC<Props> = ({ onSuccess }) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  const handleChange = async () => {
    const file = inputRef.current?.files?.[0]
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    setUploading(true)
    try {
      const res = await api.post('/upload', data)
      onSuccess?.(res.data.message)
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="flex items-center space-x-2">
      <input
        type="file"
        accept="application/pdf,image/*"
        ref={inputRef}
        hidden
        onChange={handleChange}
      />
      <button className="p-2" onClick={() => inputRef.current?.click()} disabled={uploading} title="Upload file">
        <FiUpload />
      </button>
    </div>
  )
}

export default FileUploader
