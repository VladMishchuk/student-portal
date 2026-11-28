export class ApiError extends Error {
  constructor(status, data) {
    super(`HTTP ${status}`)
    this.status = status
    this.data = data
  }
}

function csrfToken() {
  return document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith('csrftoken='))
    ?.split('=')[1]
}

export async function request(path, { method = 'GET', body } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') headers['X-CSRFToken'] = csrfToken()

  const response = await fetch(`/api/${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = response.status === 204 ? null : await response.json()
  if (!response.ok) throw new ApiError(response.status, data)
  return data
}
