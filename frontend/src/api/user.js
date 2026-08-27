import request from './request'

export const login = (data) => request.post('/users/login', data)
export const register = (data) => request.post('/users/register', data)
export const getUserInfo = () => request.get('/users/info')
export const updateUser = (data) => request.put('/users/update', data)
export const updatePassword = (data) => request.put('/users/password', data)
export const resetPassword = (data) => request.post('/users/reset-password', data)

// 本地上传头像：FormData 传文件，返回 { url }（请求拦截器会自动带 token）
export const uploadAvatar = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return request.post('/users/avatar', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
