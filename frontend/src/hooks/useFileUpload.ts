import { useState } from 'react'
import apiClient from '../api/client'

interface UploadResponse {
  job_id: string
  message: string
  file_name: string
  file_size: number
}

export function useFileUpload() {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const uploadFile = async (file: File): Promise<UploadResponse | null> => {
    setIsUploading(true)
    setUploadError(null)

    try {
      // Create form data
      const formData = new FormData()
      formData.append('file', file)

      // Upload file
      const response = await apiClient.post<UploadResponse>(
        '/chat/upload-statement',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      return response.data
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to upload file'
      setUploadError(errorMessage)
      return null
    } finally {
      setIsUploading(false)
    }
  }

  const validateFile = (file: File): string | null => {
    // Check file type
    const validTypes = [
      'text/csv',
      'application/pdf',
      'application/vnd.ms-excel',
    ]
    const validExtensions = ['.csv', '.pdf']

    const hasValidType = validTypes.includes(file.type)
    const hasValidExtension = validExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    )

    if (!hasValidType && !hasValidExtension) {
      return 'Please upload a CSV or PDF file'
    }

    // Check file size (10MB max)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      return `File size must be less than ${(maxSize / (1024 * 1024)).toFixed(0)}MB`
    }

    return null
  }

  return {
    uploadFile,
    validateFile,
    isUploading,
    uploadError,
  }
}
