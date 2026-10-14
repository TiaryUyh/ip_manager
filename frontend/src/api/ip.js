import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)))
  },
)

export function fetchIpRecords(params) {
  return http.get('/ip-records', { params }).then((res) => res.data)
}

export function fetchStats() {
  return http.get('/ip-records/stats').then((res) => res.data)
}

export function fetchCidrs() {
  return http.get('/ip-records/cidrs').then((res) => res.data)
}

export function fetchSubnetMap(cidr) {
  return http.get('/ip-records/subnet-map', { params: { cidr } }).then((res) => res.data)
}

export function createIpRecord(data) {
  return http.post('/ip-records', data).then((res) => res.data)
}

export function updateIpRecord(id, data) {
  return http.put(`/ip-records/${id}`, data).then((res) => res.data)
}

export function deleteIpRecord(id) {
  return http.delete(`/ip-records/${id}`)
}
