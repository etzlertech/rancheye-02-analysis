# Token Cost Verification Guide

## Current Implementation

### 1. Token Tracking from APIs

#### OpenAI
- **Actual token counts**: Yes, provided by API
- **Response structure**: `response.usage.prompt_tokens`, `response.usage.completion_tokens`, `response.usage.total_tokens`
- **Verification**: Console logs show exact counts: `"OpenAI token usage - Input: X, Output: Y, Total: Z"`

#### Google Gemini
- **Actual token counts**: Partial - API may provide via `response.usage_metadata`
- **Fallback**: Word count estimation if not available
- **Verification**: Console logs show: `"Gemini token usage - Input: X, Output: Y"` or `"Gemini estimated tokens: X"`

### 2. Pricing Structure (as of 2024)

```javascript
// Per 1M tokens
const costs = {
  'gpt-4o-mini': { input: 0.15, output: 0.60 },          
  'gpt-4o': { input: 5.00, output: 15.00 },              
  'gemini-1.5-flash': { input: 0.10, output: 0.40 },     
  'gemini-2.0-flash-exp': { input: 0.00, output: 0.00 }, // Free preview
  'gemini-2.5-pro': { input: 1.25, output: 10.00 }       
};
```

### 3. How to Verify Token Costs

#### A. Check Console Logs
When running an analysis, the backend logs show:
```
OpenAI token usage - Input: 324, Output: 187, Total: 511
Gemini token usage - Input: 298, Output: 165
```

#### B. Check Frontend Display
- If actual token counts are available: Shows "Input: X tokens", "Output: Y tokens", "Cost: $Z"
- If only total tokens: Shows "Tokens: X", "Est. Cost: $Z" (using 30/70 split estimate)

#### C. Manual Verification
1. **OpenAI Playground**: https://platform.openai.com/playground
   - Paste your prompt and image
   - Check token count in the interface

2. **OpenAI Tokenizer**: https://platform.openai.com/tokenizer
   - For text-only token counting

3. **Usage Dashboard**: https://platform.openai.com/usage
   - Shows actual API costs by day/model

### 4. Image Token Calculation

#### OpenAI Vision
- Low detail: 85 tokens (fixed)
- High detail: 85 + (number_of_tiles × 170)
- Default in our app: Low detail (85 tokens)

#### Gemini
- Images are processed differently, no explicit token charge
- Included in overall input token count

### 5. Database Storage

Currently storing:
- `tokens_used` - Total tokens only
- `input_tokens` - Not yet in database schema
- `output_tokens` - Not yet in database schema

To add proper tracking, run:
```sql
ALTER TABLE ai_analysis_logs 
ADD COLUMN input_tokens INTEGER,
ADD COLUMN output_tokens INTEGER;
```

### 6. Cost Accuracy

**High Confidence**:
- OpenAI costs when input/output tokens are provided
- Exact pricing matches official documentation

**Medium Confidence**:
- Gemini costs when API provides token counts
- Total token costs with estimated splits

**Low Confidence**:
- Gemini costs with word-based estimation
- Any model without actual token counts

### 7. Monitoring Recommendations

1. **Enable detailed logging** in production to capture all token counts
2. **Compare weekly** with provider billing dashboards
3. **Track cost per analysis type** to identify expensive prompts
4. **Set up alerts** for analyses exceeding expected token counts

### 8. API Response Examples

#### OpenAI Response
```json
{
  "usage": {
    "prompt_tokens": 324,
    "completion_tokens": 187,
    "total_tokens": 511
  }
}
```

#### Gemini Response (when available)
```json
{
  "usage_metadata": {
    "prompt_token_count": 298,
    "candidates_token_count": 165
  }
}
```