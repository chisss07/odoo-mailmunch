import { useState, useCallback } from 'react'
import axios from 'axios'
import api from '../api/client'
import type { LoginRequest, AuthResponse } from '../types'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('access_token')
  )
  const [error, setError] = useState('')

  const login = useCallback(async (req: LoginRequest) => {
    setError('')
    try {
      const { data } = await api.post<AuthResponse>('/auth/login', req)
      if (!data.access_token || !data.refresh_token) {
        setError('Server error: missing tokens')
        return
      }
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      // Save non-sensitive fields for form pre-fill (never store passwords/keys)
      localStorage.setItem('saved_odoo_url', req.odoo_url)
      localStorage.setItem('saved_database', req.database)
      localStorage.setItem('saved_email', req.email)
      setIsAuthenticated(true)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const status = err.response?.status
        const detail = err.response?.data?.detail
        const body = typeof err.response?.data === 'string' ? err.response.data : null
        setError(detail || body || `Login failed (HTTP ${status || 'unknown'})`)
      } else {
        setError(`Unexpected error: ${err instanceof Error ? err.message : String(err)}`)
      }
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
  }, [])

  return { isAuthenticated, error, login, logout }
}
