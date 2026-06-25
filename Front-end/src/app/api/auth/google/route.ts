import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL
  ?? process.env.API_URL
  ?? 'https://paysentineliq-production.up.railway.app/api'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    console.log('[PSI Proxy] /api/auth/google → FastAPI body:', {
      hasAccessToken: !!body.access_token,
      consentGiven: body.consent_given,
      termsVersion: body.terms_version,
    })

    const fastapiRes = await fetch(`${API_URL}/auth/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Forwarded-For': req.headers.get('x-forwarded-for') ?? '',
        'User-Agent': req.headers.get('user-agent') ?? '',
      },
      body: JSON.stringify(body),
    })

    const data = await fastapiRes.json()

    console.log('[PSI Proxy] FastAPI respondeu:', {
      status: fastapiRes.status,
      hasToken: !!data.token,
      hasAccessToken: !!data.access_token,
      hasRefreshToken: !!data.refresh_token || !!data.refreshToken,
      tokenPrefix: (data.token ?? data.access_token ?? '').substring(0, 10),
    })

    // Passa a resposta do FastAPI sem modificar
    return NextResponse.json(data, { status: fastapiRes.status })

  } catch (error) {
    console.error('[PSI Proxy] Erro ao chamar FastAPI /auth/google:', error)
    return NextResponse.json(
      { error: 'proxy_error', message: String(error) },
      { status: 502 }
    )
  }
}
