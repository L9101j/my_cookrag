import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 720000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

export default apiClient

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    console.log('发送请求：',config)
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    console.log('收到响应：',response)
    return response
  },
  error => {
    console.error('请求失败：',error)
    return Promise.reject(error)
  }
)