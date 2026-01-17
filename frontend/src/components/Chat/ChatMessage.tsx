import { format } from 'date-fns'
import { Bot, User, Info, FileText } from 'lucide-react'
import { Message } from '../../types/chat'
import clsx from 'clsx'

interface ChatMessageProps {
  message: Message
  onConfirmAccount?: (jobId: string, accountId: string) => void
  onCreateAccount?: (jobId: string, accountName: string) => void
}

export default function ChatMessage({
  message,
  onConfirmAccount,
  onCreateAccount,
}: ChatMessageProps) {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'
  const isFile = message.type === 'file'
  const isAccountConfirmation = message.type === 'account-confirmation'
  const accountMatch = message.metadata?.accountMatch
  const jobId = message.metadata?.jobId
  const statementMetadata = message.metadata?.statementMetadata

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

          {/* Account Confirmation */}
          {isAccountConfirmation && accountMatch && jobId && (
            <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
              <div className="text-sm">
                <div className="font-semibold">Suggested account</div>
                <div className="text-xs opacity-75">
                  {accountMatch.suggested_account_name ||
                    (accountMatch.should_create_new
                      ? 'New account'
                      : 'Existing account')}
                </div>
              </div>
              {statementMetadata && (
                <div className="text-xs text-gray-600">
                  {statementMetadata.institution && (
                    <span>{statementMetadata.institution}</span>
                  )}
                  {statementMetadata.account_type && (
                    <span>
                      {statementMetadata.institution ? ' · ' : ''}
                      {statementMetadata.account_type.replace('_', ' ')}
                    </span>
                  )}
                  {statementMetadata.account_number_last4 && (
                    <span>
                      {(statementMetadata.institution || statementMetadata.account_type)
                        ? ' · '
                        : ''}
                      ****{statementMetadata.account_number_last4}
                    </span>
                  )}
                </div>
              )}
              <div className="text-xs text-gray-600">
                Confidence: {(accountMatch.confidence * 100).toFixed(0)}%
              </div>
              {accountMatch.reasoning && (
                <div className="text-xs text-gray-600">{accountMatch.reasoning}</div>
              )}
              <div className="flex flex-wrap gap-2">
                {accountMatch.should_create_new && accountMatch.suggested_account_name && (
                  <button
                    className="px-3 py-2 text-xs font-semibold rounded-md bg-primary-500 text-white hover:bg-primary-600 transition"
                    onClick={() =>
                      onCreateAccount?.(jobId, accountMatch.suggested_account_name as string)
                    }
                  >
                    Create account
                  </button>
                )}
                {!accountMatch.should_create_new && accountMatch.suggested_account_id && (
                  <button
                    className="px-3 py-2 text-xs font-semibold rounded-md bg-primary-500 text-white hover:bg-primary-600 transition"
                    onClick={() =>
                      onConfirmAccount?.(jobId, accountMatch.suggested_account_id as string)
                    }
                  >
                    Use this account
                  </button>
                )}
              </div>
            </div>
          )}

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
