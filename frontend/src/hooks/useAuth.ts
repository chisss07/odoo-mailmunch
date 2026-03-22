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
      setIsAuthenticated(true)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Login failed')
      } else {
        setError('An unexpected error occurred')
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
