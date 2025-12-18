import { useState, useRef, KeyboardEvent } from 'react'
import { Send, Paperclip } from 'lucide-react'
import clsx from 'clsx'

interface ChatInputProps {
  onSendMessage: (content: string) => void
  onFileUpload: (file: File) => void
  disabled?: boolean
}

export default function ChatInput({ onSendMessage, onFileUpload, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message)
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      const validTypes = ['text/csv', 'application/pdf', 'application/vnd.ms-excel']
      if (!validTypes.includes(file.type) && !file.name.endsWith('.csv')) {
        alert('Please upload a CSV or PDF file')
        return
      }

      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB')
        return
      }

      onFileUpload(file)

      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="flex items-end gap-2">
      {/* File Upload Button */}
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        className={clsx(
          'flex-shrink-0 p-3 rounded-lg transition-colors',
          disabled
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        )}
        title="Upload bank statement"
      >
        <Paperclip className="w-5 h-5" />
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.pdf,text/csv,application/pdf"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Text Input */}
      <div className="flex-1 relative">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder={disabled ? 'Processing...' : 'Ask a question or upload a bank statement...'}
          rows={1}
          className={clsx(
            'w-full px-4 py-3 pr-12 rounded-lg border resize-none',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            disabled
              ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-white border-gray-300 text-gray-900'
          )}
          style={{ minHeight: '48px', maxHeight: '120px' }}
        />
      </div>

      {/* Send Button */}
      <button
        onClick={handleSend}
        disabled={!message.trim() || disabled}
        className={clsx(
          'flex-shrink-0 p-3 rounded-lg transition-colors',
          !message.trim() || disabled
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-primary-500 text-white hover:bg-primary-600'
        )}
        title="Send message"
      >
        <Send className="w-5 h-5" />
      </button>
    </div>
  )
}
