import http from './http'

export function scanSubnet(data) {
  return http.post('/scan/subnet', data, { timeout: 180000 }).then((res) => res.data)
}
