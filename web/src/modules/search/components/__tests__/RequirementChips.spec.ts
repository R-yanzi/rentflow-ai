import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RequirementChips from '../RequirementChips.vue'
import type { RentalRequirements } from '@/modules/search/types'

describe('RequirementChips', () => {
  it('应该展示模型提取出的硬条件和软偏好', () => {
    const requirements: RentalRequirements = {
      district: '浦东新区',
      area: '张江',
      max_rent: 7000,
      bedrooms: 2,
      pets_allowed: true,
      available_before: null,
      work_location: '陆家嘴',
      max_commute_minutes: 30,
      preferences: ['采光好'],
    }

    const wrapper = mount(RequirementChips, {
      props: {
        requirements,
      },
    })

    expect(wrapper.text()).toContain('行政区：浦东新区')
    expect(wrapper.text()).toContain('板块：张江')
    expect(wrapper.text()).toContain('最高租金：7,000 元/月')
    expect(wrapper.text()).toContain('户型：2 室')
    expect(wrapper.text()).toContain('宠物：必须允许养宠')
    expect(wrapper.text()).toContain('工作地点：陆家嘴')
    expect(wrapper.text()).toContain('偏好：采光好')
  })
})
