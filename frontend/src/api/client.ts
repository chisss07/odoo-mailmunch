import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

// Shared refresh promise to prevent concurrent 401s from triggering multiple refreshes
let refreshPromise: Promise<string> | null = null

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          // Reuse an in-flight refresh to prevent concurrent token refresh races
          if (!refreshPromise) {
            refreshPromise = axios
              .post('/api/auth/refresh', { refresh_token: refreshToken })
              .then(({ data }) => {
                localStorage.setItem('access_token', data.access_token)
                localStorage.setItem('refresh_token', data.refresh_token)
                return data.access_token as string
              })
              .finally(() => {
                refreshPromise = null
              })
          }
          const newToken = await refreshPromise
          error.config.headers.Authorization = `Bearer ${newToken}`
          return api(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
