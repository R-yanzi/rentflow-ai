import { httpClient } from '@/shared/api/http'

import type {
  NaturalLanguageSearchResponse,
  RentalRequirements,
  RequirementParseRequest,
  ConfirmedRequirementSearchRequest,
} from './types'

/**
 * 只解析自然语言，不执行房源查询。
 *
 * 后续用于“条件预览”功能，让用户确认模型提取结果。
 */
export async function parseRequirements(
  request: RequirementParseRequest,
): Promise<RentalRequirements> {
  const response = await httpClient.post<RentalRequirements>('/search/requirements', request)

  return response.data
}

/**
 * 解析自然语言，并使用可执行的硬条件搜索房源。
 */
export async function searchListings(
  request: RequirementParseRequest,
): Promise<NaturalLanguageSearchResponse> {
  const response = await httpClient.post<NaturalLanguageSearchResponse>('/search/listings', request)

  return response.data
}

/**
 * 使用用户已经确认的结构化条件搜索房源。
 *
 * 该接口不会再次调用 LLM，避免确认条件与实际执行条件不一致。
 */
export async function searchConfirmedListings(
  request: ConfirmedRequirementSearchRequest,
): Promise<NaturalLanguageSearchResponse> {
  const response = await httpClient.post<NaturalLanguageSearchResponse>(
    '/search/listings/confirmed',
    request,
  )

  return response.data
}
