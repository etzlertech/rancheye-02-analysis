# Supabase Configuration Notes

## Shared Supabase Project

Both `rancheye-01` and `rancheye-02-analysis` share the same Supabase project:

- **Project Name**: rancheye-01
- **Project ID**: enoyydytzcgejwmivshz
- **URL**: https://enoyydytzcgejwmivshz.supabase.co

## Service Responsibilities

### rancheye-01 (Camera Ingestion)
**Writes to:**
- `spypoint_images` - Image metadata and storage paths
- `spypoint_telemetry` - Camera telemetry data

### rancheye-02-analysis (AI Analysis)
**Reads from:**
- `spypoint_images` - To get images for analysis

**Writes to:**
- `analysis_configs` - Analysis configurations
- `analysis_tasks` - Task queue
- `image_analysis_results` - AI analysis results
- `analysis_alerts` - Generated alerts
- `analysis_cache` - Cached results
- `analysis_costs` - Cost tracking

## Security Notes

- Both services use the same Supabase Service Role Key for full database access
- The Service Role Key should NEVER be exposed to client-side code
- Images are stored in the `spypoint-images` bucket
- Both services can generate signed URLs for temporary image access

## Adding AI Provider Keys

To use the analysis service, you'll need to add at least one AI provider API key to the `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
GEMINI_API_KEY=...
```

Get your API keys from:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Google AI: https://makersuite.google.com/app/apikey