import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getListing } from '@/modules/listings/api'
import type { Listing } from '@/modules/listings/types'
import ListingDetailView from '@/views/ListingDetailView.vue'

/**
 * vi.mock 会被提升到文件顶部执行，因此把测试需要共享的数据
 * 放进 vi.hoisted，避免变量初始化顺序问题。
 */
const mocks = vi.hoisted(() => ({
  listingId: '00000000-0000-4000-8000-000000000001',
  back: vi.fn<() => void>(),
}))

vi.mock('@/modules/listings/api', () => ({
  /**
   * 明确声明 Mock 函数的参数和返回值，
   * 让类型检查能够保证它与真实 API 函数保持一致。
   */
  getListing: vi.fn<(listingId: string) => Promise<Listing>>(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      id: mocks.listingId,
    },
  }),
  useRouter: () => ({
    back: mocks.back,
  }),
}))

const listing: Listing = {
  id: '00000000-0000-4000-8000-000000000001',
  title: '张江南向2室1厅',
  district: '浦东新区',
  area: '张江',
  monthly_rent: 6800,
  bedrooms: 2,
  area_sqm: '78.50',
  floor: 12,
  orientation: '南',
  pets_allowed: true,
  near_main_road: false,
  available_date: '2026-12-01',
  subway_distance_m: 650,
  description: '位于小区内部，相对安静。',
  longitude: 121.606,
  latitude: 31.204,
  status: 'available',
  created_at: '2026-11-14T00:00:00Z',
  updated_at: '2026-11-14T00:00:00Z',
  distance_m: null,
}

describe('ListingDetailView', () => {
  beforeEach(() => {
    /**
     * 每个测试开始前恢复默认房源编号，并清除 Mock 的调用记录，
     * 防止测试之间相互影响。
     */
    mocks.listingId = listing.id
    vi.clearAllMocks()
  })

  it('应该请求并展示房源完整信息', async () => {
    vi.mocked(getListing).mockResolvedValue(listing)

    const wrapper = mount(ListingDetailView)

    /**
     * 页面在 watch 的 immediate 回调中异步请求数据，
     * flushPromises 用于等待请求及 Vue 页面更新完成。
     */
    await flushPromises()

    expect(getListing).toHaveBeenCalledExactlyOnceWith(listing.id)

    expect(wrapper.text()).toContain('张江南向2室1厅')
    expect(wrapper.text()).toContain('浦东新区 · 张江')
    expect(wrapper.text()).toContain('¥6,800')
    expect(wrapper.text()).toContain('78.5 ㎡')
    expect(wrapper.text()).toContain('允许养宠')
    expect(wrapper.text()).toContain('121.606')
    expect(wrapper.text()).toContain('31.204')
  })

  it('房源编号格式错误时不应该请求后端', async () => {
    mocks.listingId = 'not-a-uuid'

    const wrapper = mount(ListingDetailView)

    await flushPromises()

    expect(getListing).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('房源编号格式无效')
  })

  it('后端返回 404 时应该展示房源不存在提示', async () => {
    vi.mocked(getListing).mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 404,
      },
    })

    const wrapper = mount(ListingDetailView)

    await flushPromises()

    expect(getListing).toHaveBeenCalledExactlyOnceWith(listing.id)
    expect(wrapper.text()).toContain('该房源不存在或已被删除。')
  })

  it('点击返回按钮时应该调用浏览器历史返回', async () => {
    vi.mocked(getListing).mockResolvedValue(listing)

    const wrapper = mount(ListingDetailView)

    await flushPromises()
    await wrapper.get('.back-button').trigger('click')

    expect(mocks.back).toHaveBeenCalledOnce()
  })
})
