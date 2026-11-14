/**
 * 与后端 ListingStatus 保持一致。
 */
export type ListingStatus = 'available' | 'reserved' | 'rented' | 'offline'

/**
 * 对应后端 ListingResponse。
 *
 * UUID、日期和时间在 JSON 中均以字符串传输。
 * Decimal 为避免浮点精度丢失，也按照字符串接收。
 */
export interface Listing {
  id: string
  title: string
  district: string
  monthly_rent: number
  bedrooms: number
  area_sqm: string
  floor: number | null
  orientation: string | null
  pets_allowed: boolean
  near_main_road: boolean
  available_date: string
  subway_distance_m: number | null
  description: string
  longitude: number
  latitude: number
  status: ListingStatus
  created_at: string
  updated_at: string
  distance_m: number | null
  area: string
}

/**
 * 后端使用 limit + offset 返回的分页结果。
 */
export interface ListingListResponse {
  items: Listing[]
  total: number
  limit: number
  offset: number
}
