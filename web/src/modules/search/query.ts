import type { LocationQuery, LocationQueryRaw, LocationQueryValue } from 'vue-router'

import type { RentalRequirements } from './types'

type QueryValue = LocationQueryValue | LocationQueryValue[] | undefined

export interface SearchRouteState {
  requirements: RentalRequirements
  page: number
}

/**
 * 把可选查询参数转换成单个非空字符串。
 */
function readString(value: QueryValue): string | null {
  const firstValue = Array.isArray(value) ? value[0] : value

  if (typeof firstValue !== 'string') {
    return null
  }

  const normalizedValue = firstValue.trim()
  return normalizedValue || null
}

/**
 * 解析大于等于 0 的整数。
 */
function readNonNegativeInteger(value: QueryValue): number | null {
  const rawValue = readString(value)

  if (rawValue === null) {
    return null
  }

  const parsedValue = Number(rawValue)

  if (!Number.isInteger(parsedValue) || parsedValue < 0) {
    return null
  }

  return parsedValue
}

/**
 * 解析大于 0 的整数。
 */
function readPositiveInteger(value: QueryValue): number | null {
  const parsedValue = readNonNegativeInteger(value)

  if (parsedValue === null || parsedValue === 0) {
    return null
  }

  return parsedValue
}

/**
 * 把已确认的条件写入 URL。
 *
 * null 字段不写入 URL，避免产生大量无意义参数。
 */
export function requirementsToQuery(requirements: RentalRequirements, page = 1): LocationQueryRaw {
  return {
    district: requirements.district ?? undefined,
    area: requirements.area ?? undefined,
    max_rent: requirements.max_rent?.toString(),
    bedrooms: requirements.bedrooms?.toString(),
    pets_allowed:
      requirements.pets_allowed === null ? undefined : requirements.pets_allowed.toString(),
    available_before: requirements.available_before ?? undefined,
    work_location: requirements.work_location ?? undefined,
    max_commute_minutes: requirements.max_commute_minutes?.toString(),
    preferences: requirements.preferences.length > 0 ? requirements.preferences : undefined,
    page: page.toString(),
  }
}

/**
 * 从 URL 恢复结构化需求和当前页码。
 *
 * 浏览器 URL 属于外部输入，不能直接断言类型；
 * 非法数字和布尔值会退回安全默认值。
 */
export function searchStateFromQuery(query: LocationQuery): SearchRouteState {
  const rawPreferences = query.preferences
  const preferenceValues = Array.isArray(rawPreferences) ? rawPreferences : [rawPreferences]

  const preferences = preferenceValues
    .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
    .map((value) => value.trim())

  const rawPetsAllowed = readString(query.pets_allowed)

  let petsAllowed: boolean | null = null

  if (rawPetsAllowed === 'true') {
    petsAllowed = true
  } else if (rawPetsAllowed === 'false') {
    petsAllowed = false
  }

  return {
    requirements: {
      district: readString(query.district),
      area: readString(query.area),
      max_rent: readPositiveInteger(query.max_rent),
      bedrooms: readNonNegativeInteger(query.bedrooms),
      pets_allowed: petsAllowed,
      available_before: readString(query.available_before),
      work_location: readString(query.work_location),
      max_commute_minutes: readPositiveInteger(query.max_commute_minutes),
      preferences,
    },
    page: readPositiveInteger(query.page) ?? 1,
  }
}
