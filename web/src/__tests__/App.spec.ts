import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import HomeView from '@/views/HomeView.vue'

describe('HomeView', () => {
  it('应该展示产品名称和核心定位', () => {
    const wrapper = mount(HomeView)

    expect(wrapper.get('h1').text()).toBe('RentFlow AI')
    expect(wrapper.text()).toContain('智能决策与房源推荐平台')
  })
})
