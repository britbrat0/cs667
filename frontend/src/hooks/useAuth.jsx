import { createContext, useContext, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'))

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const t = res.data.access_token
    localStorage.setItem('token', t)
    setToken(t)
    return t
  }

  const register = async (email, password) => {
    const res = await api.post('/auth/register', { email, password })
    const t = res.data.access_token
    localStorage.setItem('token', t)
    setToken(t)
    return t
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  const isAuthenticated = !!token

  return (
    <AuthContext.Provider value={{ token, login, register, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
