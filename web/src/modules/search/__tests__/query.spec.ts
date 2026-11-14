import { describe, expect, it } from 'vitest'
import type { LocationQuery } from 'vue-router'

import { requirementsToQuery, searchStateFromQuery } from '../query'
import type { RentalRequirements } from '../types'

describe('search query conversion', () => {
  it('应该能够通过 URL 恢复完整搜索条件和页码', () => {
    const requirements: RentalRequirements = {
      district: '浦东新区',
      area: '张江',
      max_rent: 7000,
      bedrooms: 2,
      pets_allowed: true,
      available_before: '2026-12-01',
      work_location: '陆家嘴',
      max_commute_minutes: 30,
      preferences: ['采光好', '安静'],
    }

    const query = requirementsToQuery(requirements, 2) as LocationQuery

    expect(searchStateFromQuery(query)).toEqual({
      requirements,
      page: 2,
    })
  })

  it('非法查询参数应该退回安全默认值', () => {
    const query: LocationQuery = {
      max_rent: 'not-a-number',
      bedrooms: '-1',
      pets_allowed: 'unknown',
      page: '0',
    }

    const state = searchStateFromQuery(query)

    expect(state.requirements.max_rent).toBeNull()
    expect(state.requirements.bedrooms).toBeNull()
    expect(state.requirements.pets_allowed).toBeNull()
    expect(state.page).toBe(1)
  })
})
