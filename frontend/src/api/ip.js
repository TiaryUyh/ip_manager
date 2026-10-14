import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)))
  },
)

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function filenameFromDisposition(disposition, fallback) {
  if (!disposition) return fallback
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1])
  }
  const match = disposition.match(/filename="?([^"]+)"?/i)
  return match?.[1] || fallback
}

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

export async function exportIpRecords(params) {
  const response = await http.get('/ip-records/export', {
    params,
    responseType: 'blob',
  })
  const fallback =
    params.format === 'csv'
      ? 'ip_records.csv'
      : 'ip_records.xlsx'
  const filename = filenameFromDisposition(
    response.headers['content-disposition'],
    fallback,
  )
  downloadBlob(response.data, filename)
}

export async function downloadImportTemplate(format = 'xlsx') {
  const response = await http.get('/ip-records/import/template', {
    params: { format },
    responseType: 'blob',
  })
  const fallback =
    format === 'csv' ? 'ip_import_template.csv' : 'ip_import_template.xlsx'
  const filename = filenameFromDisposition(
    response.headers['content-disposition'],
    fallback,
  )
  downloadBlob(response.data, filename)
}

export function importIpRecords(file) {
  const formData = new FormData()
  formData.append('file', file)
  return http
    .post('/ip-records/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((res) => res.data)
}
