import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ListingCard from '../ListingCard.vue'
import type { Listing } from '@/modules/listings/types'

const listing: Listing = {
  id: '00000000-0000-0000-0000-000000000001',
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

describe('ListingCard', () => {
  it('应该展示房源的关键事实和合成数据标识', () => {
    const wrapper = mount(ListingCard, {
      props: {
        listing,
      },
    })

    expect(wrapper.text()).toContain('张江南向2室1厅')
    expect(wrapper.text()).toContain('浦东新区 · 张江')
    expect(wrapper.text()).toContain('¥6,800')
    expect(wrapper.text()).toContain('78.5 ㎡')
    expect(wrapper.text()).toContain('允许养宠')
    expect(wrapper.text()).toContain('演示合成数据')
  })

  it('鼠标进入卡片时应该通知父组件选中该房源', async () => {
    const wrapper = mount(ListingCard, {
      props: {
        listing,
      },
    })

    await wrapper.get('.listing-card-wrapper').trigger('mouseenter')

    expect(wrapper.emitted('select')).toEqual([[listing.id]])
  })

  it('选中房源应该展示高亮样式', () => {
    const wrapper = mount(ListingCard, {
      props: {
        listing,
        selected: true,
      },
    })

    expect(wrapper.get('.listing-card-wrapper').classes()).toContain(
      'listing-card-wrapper--selected',
    )
  })
})
