import request from './request'

export const checkFavorite = (newsId) =>
  request.get('/favorite/check', { params: { newsId } })

// 批量检查收藏状态：一次查询一批新闻 id 里已收藏的集合（列表页加载后调用）
export const batchCheckFavorite = (newsIds) =>
  request.post('/favorite/batch-check', { newsIds })

export const addFavorite = (newsId) => request.post('/favorite/add', { newsId })

export const removeFavorite = (newsId) =>
  request.delete('/favorite/remove', { params: { newsId } })

export const getFavoriteList = (page, pageSize = 10) =>
  request.get('/favorite/list', { params: { page, pageSize } })

export const clearFavorites = () => request.delete('/favorite/clear')
