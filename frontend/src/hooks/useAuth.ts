import { useState, useCallback } from 'react'
import axios from 'axios'
import api from '../api/client'
import type { LoginRequest, TOTPRequest, AuthResponse } from '../types'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('access_token')
  )
  const [needsTotp, setNeedsTotp] = useState(false)
  const [totpSession, setTotpSession] = useState('')
  const [error, setError] = useState('')

  const login = useCallback(async (req: LoginRequest) => {
    setError('')
    try {
      const { data } = await api.post<AuthResponse>('/auth/login', req)
      if (data.needs_totp) {
        if (!data.totp_session) {
          setError('Server error: missing TOTP session')
          return
        }
        setNeedsTotp(true)
        setTotpSession(data.totp_session)
      } else {
        if (!data.access_token || !data.refresh_token) {
          setError('Server error: missing tokens')
          return
        }
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        setIsAuthenticated(true)
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Login failed')
      } else {
        setError('An unexpected error occurred')
      }
    }
  }, [])

  const submitTotp = useCallback(async (code: string) => {
    setError('')
    try {
      const req: TOTPRequest = { totp_session: totpSession, totp_code: code }
      const { data } = await api.post<AuthResponse>('/auth/totp', req)
      if (!data.access_token || !data.refresh_token) {
        setError('Server error: missing tokens')
        return
      }
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      setIsAuthenticated(true)
      setNeedsTotp(false)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Invalid TOTP code')
      } else {
        setError('An unexpected error occurred')
      }
    }
  }, [totpSession])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
  }, [])

  return { isAuthenticated, needsTotp, error, login, submitTotp, logout }
}
