#!/bin/bash
# Reload Supabase schema cache
# This should be run after migrations to refresh PostgREST schema

echo "🔄 Reloading Supabase schema cache..."
echo ""
echo "Please run this command in your Supabase Dashboard SQL Editor:"
echo ""
echo "  NOTIFY pgrst, 'reload schema';"
echo ""
echo "Or restart your Supabase project in the dashboard:"
echo "  Settings → Database → Restart database"
echo ""
echo "Then re-run the tests after the cache has been reloaded."