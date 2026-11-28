import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from '../api.js'

afterEach(() => {
  vi.unstubAllGlobals()
  document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT'
})

describe('request', () => {
  it('додає X-CSRFToken лише для запитів, що змінюють дані', async () => {
    document.cookie = 'csrftoken=abc123'
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ results: [] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await request('students/')
    expect(fetchMock).toHaveBeenCalledWith('/api/students/', {
      method: 'GET',
      headers: { Accept: 'application/json' },
      body: undefined,
    })

    await request('students/', { method: 'POST', body: { first_name: 'Олена' } })
    expect(fetchMock).toHaveBeenLastCalledWith('/api/students/', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': 'abc123',
      },
      body: JSON.stringify({ first_name: 'Олена' }),
    })
  })

  it('повертає null для відповіді 204', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
      }),
    )

    const result = await request('students/1/', { method: 'DELETE' })
    expect(result).toBeNull()
  })

  it('викидає ApiError зі status і data для 403', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Немає прав' }),
      }),
    )

    await expect(request('students/1/', { method: 'DELETE' })).rejects.toMatchObject({
      status: 403,
      data: { detail: 'Немає прав' },
    })

    try {
      await request('students/1/', { method: 'DELETE' })
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError)
      expect(error.status).toBe(403)
      expect(error.data).toEqual({ detail: 'Немає прав' })
    }
  })
})
