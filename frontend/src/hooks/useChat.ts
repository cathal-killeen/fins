import { useState, useCallback } from 'react'
import { Message } from '../types/chat'
import apiClient from '../api/client'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: "Hi! I'm your AI financial assistant. Upload a bank statement (CSV or PDF) and I'll help you import your transactions. Or ask me anything about your finances!",
      timestamp: new Date(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message])
  }, [])

  const updateMessage = useCallback((id: string, updates: Partial<Message>) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      )
    )
  }, [])

  const sendMessage = useCallback(
    async (content: string) => {
      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content,
        timestamp: new Date(),
      }
      addMessage(userMessage)

      setIsLoading(true)

      try {
        // Call AI chat API
        const response = await apiClient.post('/ai/chat', {
          message: content,
        })

        // Add AI response
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
        }
        addMessage(assistantMessage)
      } catch (error) {
        // Add error message
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'system',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date(),
        }
        addMessage(errorMessage)
        console.error('Error sending message:', error)
      } finally {
        setIsLoading(false)
      }
    },
    [addMessage]
  )

  return {
    messages,
    isLoading,
    sendMessage,
    addMessage,
    updateMessage,
  }
}
