// 相对时间：x 分钟前 / x 小时前 / x 天前 / 日期
export function formatRelativeTime(timeStr) {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  if (Number.isNaN(d.getTime())) return timeStr
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour} 小时前`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day} 天前`
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

// 浏览量缩写：1.2万
export function formatViews(n) {
  if (n == null || Number.isNaN(Number(n))) return '0'
  const num = Number(n)
  if (num >= 10000) return `${(num / 10000).toFixed(1).replace(/\.0$/, '')}万`
  return String(num)
}

// 完整时间：2026-08-18 14:30
export function formatDateTime(timeStr) {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  if (Number.isNaN(d.getTime())) return timeStr
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${dd} ${hh}:${mm}`
}
