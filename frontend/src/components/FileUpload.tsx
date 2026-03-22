import { useState, useRef } from 'react'
import axios from 'axios'
import api from '../api/client'

interface FileUploadProps {
  onUploaded?: () => void
}

export default function FileUpload({ onUploaded }: FileUploadProps) {
  const [dragging, setDragging] = useState(false)
  const [pasteMode, setPasteMode] = useState(false)
  const [pasteText, setPasteText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFiles = async (files: FileList) => {
    setUploading(true)
    setMessage('')
    try {
      for (const file of Array.from(files)) {
        const form = new FormData()
        form.append('file', file)
        await api.post('/emails/upload', form)
      }
      setMessage(`${files.length} file(s) uploaded`)
      onUploaded?.()
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : null
      setMessage(detail || `Upload failed (${axios.isAxiosError(err) ? `HTTP ${err.response?.status}` : 'unknown error'})`)
    } finally {
      setUploading(false)
    }
  }

  const handlePaste = async () => {
    if (!pasteText.trim()) return
    setUploading(true)
    try {
      await api.post('/emails/paste', { text: pasteText })
      setPasteText('')
      setPasteMode(false)
      setMessage('Email submitted')
      onUploaded?.()
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : null
      setMessage(detail || 'Submit failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mb-6">
      {pasteMode ? (
        <div className="bg-surface-light rounded-lg p-4">
          <h3 className="text-white font-medium mb-2">Paste Email Text</h3>
          <textarea
            value={pasteText}
            onChange={e => setPasteText(e.target.value)}
            rows={8}
            className="w-full bg-surface border border-white/20 text-white text-sm px-3 py-2 rounded font-mono focus:outline-none focus:border-primary"
            placeholder="Paste email content here..."
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handlePaste}
              disabled={uploading}
              className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded text-sm"
            >
              {uploading ? 'Submitting...' : 'Submit'}
            </button>
            <button
              onClick={() => setPasteMode(false)}
              className="text-white/60 hover:text-white px-4 py-2 rounded text-sm border border-white/20"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            dragging ? 'border-primary bg-primary/5' : 'border-white/20 hover:border-white/40'
          }`}
          onDragOver={e => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => {
            e.preventDefault()
            setDragging(false)
            if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files)
          }}
          onClick={() => fileRef.current?.click()}
        >
          <p className="text-white/60 text-sm">Drop .eml, .msg, .pdf files here, or click to browse</p>
          <div className="flex justify-center gap-3 mt-3">
            <span className="text-white/30 text-xs">or</span>
            <button
              onClick={e => {
                e.stopPropagation()
                setPasteMode(true)
              }}
              className="text-primary text-xs hover:underline"
            >
              Paste email text
            </button>
          </div>
          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".eml,.msg,.pdf,.xlsx"
            className="hidden"
            onChange={e => e.target.files && handleFiles(e.target.files)}
          />
        </div>
      )}
      {message && <p className="text-white/60 text-xs mt-2">{message}</p>}
    </div>
  )
}
