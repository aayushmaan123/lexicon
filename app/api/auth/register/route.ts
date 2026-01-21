import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const { email, password, name } = await request.json();
    
    // Basic validation
    if (!email || !password || !name) {
      return NextResponse.json(
        { error: "Email, password, and name are required" },
        { status: 400 }
      );
    }
    
    // TODO: Implement Supabase user registration
    console.log("Registration attempt for:", email, name);
    return NextResponse.json({
      message: "Register endpoint - implementation pending",
      email,
      name,
    });
  } catch (error) {
    return NextResponse.json(
      { error: "Registration failed" },
      { status: 500 }
    );
  }
}
