import type { AnalyzeRequest, AnalyzeResponse } from '../types/game'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function analyzeHand(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch (err) {
    throw new Error(
      `Network error: cannot reach API at ${API_BASE}. Ensure backend is running and CORS is enabled. (${(err as Error).message})`,
    )
  }

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      const body = (await response.json()) as { detail?: unknown }
      const detail =
        typeof body.detail === 'string'
          ? body.detail
          : Array.isArray(body.detail)
            ? body.detail.map((item) => JSON.stringify(item)).join('; ')
            : JSON.stringify(body.detail)
      throw new Error(`Analyze failed (${response.status}): ${detail}`)
    }
    const text = await response.text()
    throw new Error(`Analyze failed (${response.status}): ${text}`)
  }

  return (await response.json()) as AnalyzeResponse
}
