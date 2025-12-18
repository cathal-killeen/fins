import { useState, useRef, useEffect } from 'react'
import { Message } from '../../types/chat'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import { useFileUpload } from '../../hooks/useFileUpload'
import { useChat } from '../../hooks/useChat'

export default function ChatInterface() {
  const { messages, isLoading, sendMessage, addMessage } = useChat()
  const { uploadFile, validateFile, isUploading } = useFileUpload()
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (content: string) => {
    await sendMessage(content)
  }

  const handleFileUpload = async (file: File) => {
    // Validate file
    const validationError = validateFile(file)
    if (validationError) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'system',
        content: validationError,
        timestamp: new Date(),
      }
      addMessage(errorMessage)
      return
    }

    // Add file upload message
    const fileMessage: Message = {
      id: Date.now().toString(),
      type: 'file',
      content: `Uploading ${file.name}...`,
      timestamp: new Date(),
      metadata: {
        fileInfo: {
          name: file.name,
          size: file.size,
          type: file.type,
        },
      },
    }
    addMessage(fileMessage)
    setIsProcessing(true)

    // Upload file
    const result = await uploadFile(file)

    if (result) {
      // Success - file uploaded
      const successMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `✓ ${result.file_name} uploaded successfully! Processing your statement...`,
        timestamp: new Date(),
        metadata: {
          jobId: result.job_id,
          processingStatus: {
            stage: 'Uploading',
            progress: 10,
            message: 'File uploaded, starting analysis...',
          },
        },
      }
      addMessage(successMessage)

      // TODO: Start polling for status updates
    } else {
      // Error - show error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: 'Failed to upload file. Please try again.',
        timestamp: new Date(),
      }
      addMessage(errorMessage)
    }

    setIsProcessing(false)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Fins AI Assistant</h1>
        <p className="text-sm text-gray-500">Upload statements or ask questions about your finances</p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            disabled={isProcessing || isLoading || isUploading}
          />
        </div>
      </div>
    </div>
  )
}
