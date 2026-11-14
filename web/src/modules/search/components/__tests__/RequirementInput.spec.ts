import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RequirementInput from '../RequirementInput.vue'

describe('RequirementInput', () => {
  it('提交时应该去除输入内容两侧的空格', async () => {
    const wrapper = mount(RequirementInput)

    await wrapper.get('textarea').setValue('  预算 7000 元以内  ')
    await wrapper.get('.submit-button').trigger('click')

    expect(wrapper.emitted('submit')).toEqual([['预算 7000 元以内']])
  })

  it('输入为空时不应该提交', async () => {
    const wrapper = mount(RequirementInput)

    await wrapper.get('textarea').setValue('   ')
    await wrapper.get('.submit-button').trigger('click')

    expect(wrapper.emitted('submit')).toBeUndefined()
  })
})
