import request from './request'

export const checkFavorite = (newsId) =>
  request.get('/favorite/check', { params: { newsId } })

export const addFavorite = (newsId) => request.post('/favorite/add', { newsId })

export const removeFavorite = (newsId) =>
  request.delete('/favorite/remove', { params: { newsId } })

export const getFavoriteList = (page, pageSize = 10) =>
  request.get('/favorite/list', { params: { page, pageSize } })

export const clearFavorites = () => request.delete('/favorite/clear')
