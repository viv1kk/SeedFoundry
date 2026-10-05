// JSON over /api (Vite proxies it to the backend, so the browser sees one origin).
// Errors carry the server's `{"detail": {"code", "message", ...}}` body (D-35), so the UI can
// show the message as written.

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly detail: Record<string, unknown>

  constructor(status: number, code: string, message: string, detail: Record<string, unknown> = {}) {
    super(message)
    this.status = status
    this.code = code
    this.detail = detail
  }
}

async function failure(response: Response): Promise<ApiError> {
  let detail: unknown = null
  try {
    detail = ((await response.json()) as { detail?: unknown }).detail
  } catch {
    // Not JSON: fall through to a generic message.
  }
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const body = detail as Record<string, unknown>
    if (typeof body.code === 'string' && typeof body.message === 'string') {
      return new ApiError(response.status, body.code, body.message, body)
    }
  }
  // FastAPI's own validation errors (422 with a list) and anything else.
  return new ApiError(response.status, 'request_failed', `The server refused the request (${response.status}).`)
}

export interface RequestOptions {
  method?: string
  json?: unknown
  body?: BodyInit
  keepalive?: boolean
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const init: RequestInit = { method: options.method ?? 'GET', keepalive: options.keepalive }
  if (options.json !== undefined) {
    init.headers = { 'Content-Type': 'application/json' }
    init.body = JSON.stringify(options.json)
  } else if (options.body !== undefined) {
    init.headers = { 'Content-Type': 'application/octet-stream' }
    init.body = options.body
  }
  let response: Response
  try {
    response = await fetch(path, init)
  } catch {
    throw new ApiError(0, 'offline', 'Cannot reach the SeedFactory server.')
  }
  if (!response.ok) throw await failure(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

/** The error's message for the UI. */
export function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Try again.'
}
