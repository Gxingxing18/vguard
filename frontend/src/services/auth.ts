import axios from 'axios'

const http = axios.create({
  baseURL: '',
  timeout: 15000,
})

export async function login(username: string, password: string): Promise<{ token: string; username: string }> {
  console.log('login request')
  const { data } = await http.post('/api/v1/auth/login', { username, password })
  return data
}

export async function register(username: string, password: string): Promise<{ ok: boolean }> {
  const { data } = await http.post('/api/v1/auth/register', { username, password })
  return data
}

export async function fetchMe(token: string): Promise<{ username: string }> {
  const { data } = await http.get('/api/v1/auth/me', { params: { token } })
  return data
}

export async function logout(token: string): Promise<{ ok: boolean }> {
  const { data } = await http.post('/api/v1/auth/logout', null, { params: { token } })
  return data
}
