import http from './http'

export function login(username, password) {
  return http
    .post('/auth/login', { username, password })
    .then((res) => res.data)
}

export function fetchMe() {
  return http.get('/auth/me').then((res) => res.data)
}
