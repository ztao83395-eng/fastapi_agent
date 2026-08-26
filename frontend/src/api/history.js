import request from './request'

export const addHistory = (newsId) => request.post('/history/add', { newsId })

export const getHistoryList = (page, pageSize = 10) =>
  request.get('/history/list', { params: { page, pageSize } })

export const deleteHistory = (newsId) => request.delete(`/history/delete/${newsId}`)

export const clearHistory = () => request.delete('/history/clear')
