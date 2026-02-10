"use client"

import useSWR, { type SWRConfiguration } from "swr"
import { apiClient } from "@/lib/api-client"
import type { PaginatedResponse } from "@/types/api"

const fetcher = <T,>(url: string) => apiClient.get<T>(url)

export function useList<T>(
  resource: string,
  page = 1,
  size = 10,
  search?: string,
  config?: SWRConfiguration,
) {
  const params = new URLSearchParams({
    page: String(page),
    size: String(size),
  })
  if (search) params.set("search", search)

  const key = `/api/${resource}?${params.toString()}`
  return useSWR<PaginatedResponse<T>>(key, fetcher, config)
}

export function useDetail<T>(resource: string, id: string | null, config?: SWRConfiguration) {
  const key = id ? `/api/${resource}/${id}` : null
  return useSWR<T>(key, fetcher, config)
}

export function useCRUD<T>(resource: string) {
  const create = (data: Partial<T>) => apiClient.post<T>(`/api/${resource}`, data)
  const update = (id: string, data: Partial<T>) => apiClient.put<T>(`/api/${resource}/${id}`, data)
  const remove = (id: string) => apiClient.delete(`/api/${resource}/${id}`)

  return { create, update, remove }
}
