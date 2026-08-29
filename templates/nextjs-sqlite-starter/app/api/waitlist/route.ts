import { NextResponse } from 'next/server';
import db from '@/lib/db';

export async function POST(request: Request) {
  try {
    const { email } = await request.json();
    if (!email || !email.includes('@')) {
      return NextResponse.json({ error: 'Valid email is required' }, { status: 400 });
    }

    const stmt = db.prepare('INSERT OR IGNORE INTO waitlist (email) VALUES (?)');
    const info = stmt.run(email.trim().toLowerCase());

    return NextResponse.json({ 
      success: true, 
      message: 'Successfully joined the waitlist!',
      inserted: info.changes > 0 
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
  }
}

export async function GET() {
  try {
    const stmt = db.prepare('SELECT COUNT(*) as count FROM waitlist');
    const result = stmt.get() as { count: number };
    return NextResponse.json({ count: result.count });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
