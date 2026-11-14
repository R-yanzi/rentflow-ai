import { httpClient } from '@/shared/api/http'

import type { Listing } from './types'

/**
 * 根据房源 UUID 获取完整房源事实。
 */
export async function getListing(listingId: string): Promise<Listing> {
  const response = await httpClient.get<Listing>(`/listings/${encodeURIComponent(listingId)}`)

  return response.data
}
