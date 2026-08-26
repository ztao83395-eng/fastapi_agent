// 通用分页加载逻辑：对接 van-list 触底加载 + van-pull-refresh 下拉刷新
import { ref } from 'vue'

export function usePagedList(fetchPage) {
  const list = ref([])
  const page = ref(0)
  const loading = ref(false)
  const finished = ref(false)
  const refreshing = ref(false)
  const failed = ref(false)

  async function loadPage() {
    // 注意：不能检查 loading —— van-list 触底时会先把 loading 置 true 再 emit load，
    // 若在这里检查 loading 会把每次触底加载都挡掉（一直显示"加载中"）。
    // van-list 内部自己保证 loading 为 true 期间不会重复触发，无并发风险。
    if (finished.value) return
    loading.value = true
    try {
      const next = page.value + 1
      const data = await fetchPage(next)
      list.value.push(...data.list)
      page.value = next
      finished.value = !data.hasMore
      failed.value = false
    } catch (e) {
      failed.value = true
      finished.value = true
    } finally {
      loading.value = false
      refreshing.value = false
    }
  }

  async function onRefresh() {
    page.value = 0
    list.value = []
    finished.value = false
    failed.value = false
    await loadPage()
  }

  // 外部触发刷新（如删除/清空后）
  async function refresh() {
    await onRefresh()
  }

  return { list, loading, finished, refreshing, failed, loadPage, onRefresh, refresh }
}
