export interface Account {
  id: string
  user_id: string
  account_type: string
  account_name: string
  institution?: string
  account_number_last4?: string
  currency: string
  current_balance?: number
  is_active: boolean
}

export interface Transaction {
  id: string
  account_id: string
  transaction_date: string
  amount: number
  currency: string
  description: string
  merchant_name?: string
  category?: string
  subcategory?: string
}

export interface FileInfo {
  name: string
  size: number
  type: string
}

export interface ProcessingStatus {
  stage: string
  progress: number
  message: string
}

export interface StatementMetadata {
  institution?: string
  account_type?: string
  account_number_last4?: string
}

export interface AccountMatch {
  suggested_account_id: string | null
  confidence: number
  reasoning: string
  should_create_new: boolean
  suggested_account_name?: string
}

export interface TransactionSummary {
  count: number
  dateRange: {
    start: string
    end: string
  }
  totalAmount: number
  preview: Transaction[]
}

export type MessageType =
  | 'user'
  | 'assistant'
  | 'system'
  | 'file'
  | 'account-confirmation'
  | 'transaction-summary'

export interface MessageMetadata {
  fileInfo?: FileInfo
  processingStatus?: ProcessingStatus
  accountMatch?: AccountMatch
  statementMetadata?: StatementMetadata
  transactionSummary?: TransactionSummary
  jobId?: string
}

export interface Message {
  id: string
  type: MessageType
  content: string
  timestamp: Date
  metadata?: MessageMetadata
}
