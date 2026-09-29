import axios from 'axios'
import type { AxiosInstance } from 'axios'

export interface ApiError {
  status: number
  message: string
}

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — inject API key from localStorage
client.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('api_key') ?? 'changeme'
  config.headers['X-API-Key'] = apiKey
  return config
})

// Response interceptor — normalize errors to ApiError
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError: ApiError = {
      status: error.response?.status ?? 0,
      message: error.response?.data?.detail ?? error.message ?? 'Unknown error',
    }
    return Promise.reject(apiError)
  },
)

export const http = {
  get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    return client.get<T>(url, { params }).then((r) => r.data)
  },

  post<T>(url: string, body?: unknown): Promise<T> {
    return client.post<T>(url, body).then((r) => r.data)
  },

  del<T>(url: string): Promise<T> {
    return client.delete<T>(url).then((r) => r.data)
  },
}
