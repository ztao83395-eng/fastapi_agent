import request from './request'

export const getCategories = () => request.get('/news/categories')

export const getNewsList = ({ categoryId, page, pageSize = 10 }) =>
  request.get('/news/list', { params: { categoryId, page, pageSize } })

export const getNewsDetail = (id) => request.get('/news/detail', { params: { id } })
