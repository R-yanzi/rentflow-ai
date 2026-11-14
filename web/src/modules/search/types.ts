import type { ListingListResponse } from '@/modules/listings/types'

/**
 * 用户提交给自然语言解析接口的请求。
 */
export interface RequirementParseRequest {
  text: string
}

/**
 * DeepSeek 从自然语言中提取出的结构化租房需求。
 *
 * null 表示用户没有提供该条件，前端不能擅自补充。
 */
export interface RentalRequirements {
  district: string | null
  area: string | null
  max_rent: number | null
  bedrooms: number | null
  pets_allowed: boolean | null
  available_before: string | null
  work_location: string | null
  max_commute_minutes: number | null
  preferences: string[]
}

/**
 * 使用已确认条件执行分页搜索的请求。
 *
 * requirements 是用户确认的业务条件；
 * limit 和 offset 是本次列表查询的分页控制参数。
 */
export interface ConfirmedRequirementSearchRequest {
  requirements: RentalRequirements
  limit: number
  offset: number
}

/**
 * 自然语言搜索的完整响应。
 */
export interface NaturalLanguageSearchResponse {
  requirements: RentalRequirements
  results: ListingListResponse

  /**
   * 当前后端尚不能执行的条件。
   * 前端必须向用户展示，不能让用户误以为这些条件已参与筛选。
   */
  unresolved_requirements: string[]
}
