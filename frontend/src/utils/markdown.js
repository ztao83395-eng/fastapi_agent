import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ breaks: true, gfm: true })

// 将 markdown 转为消毒后的安全 HTML
export function renderMarkdown(text = '') {
  const html = marked.parse(text)
  return DOMPurify.sanitize(html)
}
