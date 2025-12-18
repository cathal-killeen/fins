import { format } from 'date-fns'
import { Bot, User, Info, FileText } from 'lucide-react'
import { Message } from '../../types/chat'
import clsx from 'clsx'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'
  const isFile = message.type === 'file'

  const getIcon = () => {
    if (isUser) return <User className="w-5 h-5" />
    if (isSystem) return <Info className="w-5 h-5" />
    if (isFile) return <FileText className="w-5 h-5" />
    return <Bot className="w-5 h-5" />
  }

  const getBackgroundColor = () => {
    if (isUser) return 'bg-primary-500 text-white'
    if (isSystem) return 'bg-gray-100 text-gray-900'
    if (isFile) return 'bg-blue-50 text-blue-900'
    return 'bg-white text-gray-900'
  }

  const getAlignment = () => {
    return isUser ? 'flex-row-reverse' : 'flex-row'
  }

  return (
    <div className={clsx('flex gap-3', getAlignment())}>
      {/* Avatar */}
      <div
        className={clsx(
          'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary-100 text-primary-600' : 'bg-gray-100 text-gray-600'
        )}
      >
        {getIcon()}
      </div>

      {/* Message Content */}
      <div className={clsx('flex flex-col max-w-xl', isUser ? 'items-end' : 'items-start')}>
        <div
          className={clsx(
            'rounded-lg px-4 py-3 shadow-sm',
            getBackgroundColor(),
            isUser ? 'rounded-tr-none' : 'rounded-tl-none'
          )}
        >
          {/* File Info */}
          {message.metadata?.fileInfo && (
            <div className="mb-2 text-sm">
              <div className="font-semibold">{message.metadata.fileInfo.name}</div>
              <div className="text-xs opacity-75">
                {(message.metadata.fileInfo.size / 1024).toFixed(1)} KB
              </div>
            </div>
          )}

          {/* Message Text */}
          <div className="whitespace-pre-wrap">{message.content}</div>

          {/* Processing Status */}
          {message.metadata?.processingStatus && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2 text-sm">
                <div className="flex-1">
                  <div className="font-medium">{message.metadata.processingStatus.stage}</div>
                  <div className="text-xs opacity-75">{message.metadata.processingStatus.message}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold">{message.metadata.processingStatus.progress}%</div>
                </div>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${message.metadata.processingStatus.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className="text-xs text-gray-500 mt-1 px-1">
          {format(message.timestamp, 'h:mm a')}
        </div>
      </div>
    </div>
  )
}
