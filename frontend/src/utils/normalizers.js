// 后端接口字段命名不统一（列表 snake_case / 详情 camelCase），
// 统一递归转为 camelCase；已是 camelCase 的字段幂等无副作用。

const toCamel = (str) => str.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase())

export function camelizeKeys(value) {
  if (Array.isArray(value)) return value.map(camelizeKeys)
  if (value !== null && typeof value === 'object' && !(value instanceof Date)) {
    return Object.keys(value).reduce((acc, key) => {
      const newKey = key.includes('_') ? toCamel(key) : key
      acc[newKey] = camelizeKeys(value[key])
      return acc
    }, {})
  }
  return value
}
