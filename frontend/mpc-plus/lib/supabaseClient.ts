// Supabase client wrapper. Initializes Supabase using NEXT_PUBLIC_* env vars.
import { createClient } from '@supabase/supabase-js';

// Use NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY for frontend-safe key
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let supabase = null as any;

if (supabaseUrl && supabasePublishableKey) {
  supabase = createClient(supabaseUrl, supabasePublishableKey);
} else {
  // supabase will be null if env vars not provided; callers should handle fallback
  supabase = null;
}

export default supabase;
