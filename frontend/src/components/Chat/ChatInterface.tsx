import { useState, useRef, useEffect, useCallback } from 'react'
import { AccountMatch, Message, StatementMetadata } from '../../types/chat'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import { useFileUpload } from '../../hooks/useFileUpload'
import { useChat } from '../../hooks/useChat'
import apiClient from '../../api/client'

interface ProcessingStatusResponse {
  job_id: string
  status: string
  current_stage: string
  progress: number
  message: string
  error?: string
  account_match?: AccountMatch
  statement_metadata?: StatementMetadata
}

export default function ChatInterface() {
  const { messages, isLoading, sendMessage, addMessage, updateMessage } = useChat()
  const { uploadFile, validateFile, isUploading } = useFileUpload()
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingJobId, setProcessingJobId] = useState<string | null>(null)
  const [processingMessageId, setProcessingMessageId] = useState<string | null>(null)
  const [hasShownAccountConfirmation, setHasShownAccountConfirmation] = useState(false)
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
      const successMessageId = (Date.now() + 1).toString()
      const successMessage: Message = {
        id: successMessageId,
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
      setProcessingJobId(result.job_id)
      setProcessingMessageId(successMessageId)
      setHasShownAccountConfirmation(false)

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

  const handleConfirmAccount = useCallback(
    async (jobId: string, accountId: string) => {
      try {
        await apiClient.post('/chat/confirm-account', {
          job_id: jobId,
          account_id: accountId,
          create_new_account: false,
        })
        addMessage({
          id: Date.now().toString(),
          type: 'system',
          content: 'Account confirmed. Continuing import...',
          timestamp: new Date(),
        })
        setProcessingJobId(jobId)
      } catch (error) {
        addMessage({
          id: Date.now().toString(),
          type: 'system',
          content: 'Failed to confirm account. Please try again.',
          timestamp: new Date(),
        })
      }
    },
    [addMessage]
  )

  const handleCreateAccount = useCallback(
    async (jobId: string, accountName: string) => {
      try {
        await apiClient.post('/chat/confirm-account', {
          job_id: jobId,
          create_new_account: true,
          new_account_name: accountName,
        })
        addMessage({
          id: Date.now().toString(),
          type: 'system',
          content: `Creating "${accountName}" and continuing import...`,
          timestamp: new Date(),
        })
        setProcessingJobId(jobId)
      } catch (error) {
        addMessage({
          id: Date.now().toString(),
          type: 'system',
          content: 'Failed to create account. Please try again.',
          timestamp: new Date(),
        })
      }
    },
    [addMessage]
  )

  useEffect(() => {
    if (!processingJobId || !processingMessageId) return

    let isMounted = true

    const pollStatus = async () => {
      try {
        const response = await apiClient.get<ProcessingStatusResponse>(
          `/chat/processing-status/${processingJobId}`
        )

        if (!isMounted) return

        const status = response.data
        const nextStage = status.current_stage || status.status

        updateMessage(processingMessageId, {
          metadata: {
            jobId: processingJobId,
            processingStatus: {
              stage: nextStage,
              progress: status.progress,
              message: status.message,
            },
          },
        })

        if (
          nextStage === 'awaiting_confirmation' &&
          status.account_match &&
          !hasShownAccountConfirmation
        ) {
          addMessage({
            id: `${processingJobId}-confirm`,
            type: 'account-confirmation',
            content: status.account_match.should_create_new
              ? 'No matching account found. Would you like to create a new one?'
              : 'We found a likely matching account. Please confirm to continue.',
            timestamp: new Date(),
            metadata: {
              accountMatch: status.account_match,
              statementMetadata: status.statement_metadata,
              jobId: processingJobId,
            },
          })
          setHasShownAccountConfirmation(true)
          setProcessingJobId(null)
        }

        if (status.status === 'failed') {
          addMessage({
            id: `${processingJobId}-failed`,
            type: 'system',
            content: status.error || 'Statement processing failed.',
            timestamp: new Date(),
          })
          setProcessingJobId(null)
        }

        if (status.status === 'completed') {
          addMessage({
            id: `${processingJobId}-completed`,
            type: 'system',
            content: 'Statement import completed.',
            timestamp: new Date(),
          })
          setProcessingJobId(null)
        }
      } catch (error) {
        if (!isMounted) return
        addMessage({
          id: `${processingJobId}-error`,
          type: 'system',
          content: 'Failed to fetch processing status.',
          timestamp: new Date(),
        })
        setProcessingJobId(null)
      }
    }

    pollStatus()
    const interval = setInterval(pollStatus, 2000)

    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [
    addMessage,
    hasShownAccountConfirmation,
    processingJobId,
    processingMessageId,
    updateMessage,
  ])

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
            <ChatMessage
              key={message.id}
              message={message}
              onConfirmAccount={handleConfirmAccount}
              onCreateAccount={handleCreateAccount}
            />
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
