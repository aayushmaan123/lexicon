import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    // TODO: Implement search logic with DeepSeek, Gemini, Tavily
    return NextResponse.json({
      results: [],
      total: 0,
      query: body.query,
      processingTime: 0,
    });
  } catch (error) {
    return NextResponse.json({ error: "Search failed" }, { status: 500 });
  }
}
