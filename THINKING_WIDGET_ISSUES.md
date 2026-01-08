# Thinking Widget Issues - Root Cause Analysis

## Problem Summary

The thinking widget is not showing up for DeepSeek-R1 and Kimi-K2 models because:

1. **Wrong model name**: Using `deepseek-r1` instead of `deepseek-reasoner`
2. **API proxy limitation**: nano-gpt.com may not pass through `reasoning_content` field
3. **Model format differences**: Different models use different formats for reasoning

## What We Found

### Test Results

Using `./test_thinking_models.py deepseek-r1` showed:
- NO `reasoning_content` field in the response
- Only regular `content` field with the final answer
- Delta keys: `['content']` only

This means the nano-gpt.com API is either:
- Not using the correct DeepSeek model name
- Not passing through the `reasoning_content` field
- Not supporting DeepSeek's reasoning format

## Solution

### Option 1: Use DeepSeek Direct API (Recommended)

The DeepSeek API documentation shows that the correct model name is **`deepseek-reasoner`**, and it should return both `reasoning_content` and `content` fields.

**Test with DeepSeek directly:**

```bash
# Set your DeepSeek API key
export DEEPSEEK_API_KEY='your-deepseek-api-key'

# Test direct connection
./test_deepseek_direct.py
```

This will show if DeepSeek's reasoning actually works when not going through the nano-gpt proxy.

### Option 2: Check nano-gpt.com Support

Ask nano-gpt.com:
1. Do they support `reasoning_content` field?
2. What's the correct model name for DeepSeek reasoning models?
3. Can they pass through the full DeepSeek API response?

### Option 3: Use a Different Model Provider

If nano-gpt.com doesn't support reasoning models:
- Use DeepSeek directly: `https://api.deepseek.com`
- Use OpenAI's o1 models: `https://api.openai.com/v1`
- Use other providers that support reasoning fields

## Model-Specific Information

### DeepSeek Reasoning Models

- **Correct model name**: `deepseek-reasoner`
- **API endpoint**: `https://api.deepseek.com`
- **Response format**:
  ```json
  {
    "choices": [{
      "delta": {
        "reasoning_content": "Thinking process...",
        "content": "Final answer..."
      }
    }]
  }
  ```

- **Documentation**: [DeepSeek Reasoning Model Docs](https://api-docs.deepseek.com/guides/reasoning_model)

### OpenAI o1/o3 Models

- **Model names**: `o1`, `o1-mini`, `o1-preview`, `o3-mini`
- **API endpoint**: `https://api.openai.com/v1`
- **Response format**: Same as DeepSeek (reasoning_content field)

### Kimi-K2

- Need to check Moonshot AI's documentation for their reasoning format
- May use different field names or API structure

## Testing Checklist

- [ ] Test with `deepseek-reasoner` model name
- [ ] Test with DeepSeek direct API (not through nano-gpt)
- [ ] Test with OpenAI o1 models if available
- [ ] Check nano-gpt.com documentation for reasoning model support
- [ ] Verify API response includes `reasoning_content` field

## Code Changes Made

### 1. Added Logging (nanochat/api/client.py:287-292)
Logs all delta fields when reasoning or thinking content is detected.

### 2. Added Content Tracking (nanochat/state/app_state.py:341-344)
Logs when thinking content is being yielded to the UI.

### 3. Enhanced Widget Updates (nanochat/ui/chat_view.py:1425-1437)
Improved thinking widget update logic to avoid unnecessary updates.

### 4. Auto-Expand Widget (nanochat/ui/thinking_widget.py:72-79)
Thinking widget now auto-expands when it receives content.

## Next Steps

1. Run `./test_deepseek_direct.py` with a DeepSeek API key
2. If that works, the issue is with nano-gpt.com not supporting reasoning models
3. Consider adding a configuration option to use direct model APIs
4. Add support for multiple reasoning model formats

## Sources

- [DeepSeek Reasoning Model Documentation](https://api-docs.deepseek.com/guides/reasoning_model)
- [DeepSeek Thinking Mode Guide](https://api-docs.deepseek.com/guides/thinking_mode)
- [vLLM Reasoning Outputs](https://docs.vllm.ai/en/latest/features/reasoning_outputs/)
