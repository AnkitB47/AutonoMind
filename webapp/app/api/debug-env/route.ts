import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({ env: process.env.NEXT_PUBLIC_FASTAPI_URL });
}
