import request from './request'

export const login = (data) => request.post('/users/login', data)
export const register = (data) => request.post('/users/register', data)
export const getUserInfo = () => request.get('/users/info')
export const updateUser = (data) => request.put('/users/update', data)
export const updatePassword = (data) => request.put('/users/password', data)
