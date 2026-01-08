# How to Enable Thinking Widget with NanoGPT API

## The Fix is Complete! ✅

I've updated `nanochat/api/client.py` to support BOTH reasoning field formats:
- `reasoning_content` (OpenAI/DeepSeek direct API format)
- `reasoning` (NanoGPT API format)

## How to Use with NanoGPT

### Option 1: Use Model Suffix (Recommended)

Append `:thinking` to your model name in settings to enable reasoning mode:

**For DeepSeek models:**
```
deepseek-r1:thinking
deepseek-reasoner:thinking
```

**For Claude models:**
```
claude-3-5-sonnet-20241022:thinking
claude-3-7-sonnet-20250620:thinking
```

**For GPT models:**
```
gpt-4o:thinking
o3-mini:thinking
```

### Option 2: Use `reasoning_effort` Parameter

Control how much computational effort goes into reasoning:

```python
# In your settings or when calling the API:
{
    "model": "deepseek-r1",
    "reasoning_effort": "high"  # Options: none, minimal, low, medium, high
}
```

**Effort levels:**
- `none` - Disables reasoning entirely
- `minimal` - ~10% of max_tokens for reasoning
- `low` - ~20% of max_tokens for reasoning
- `medium` - ~50% of max_tokens for reasoning (default)
- `high` - ~80% of max_tokens for reasoning

### Option 3: Combine with Other Features

You can combine `:thinking` with other NanoGPT suffixes:

```
deepseek-r1:thinking:online          # Thinking + web search
deepseek-r1:thinking:memory           # Thinking + context memory
gpt-4o:thinking:online:memory        # All features combined
```

## Testing

1. **Open Settings** (Ctrl+,)
2. **Change model** to a thinking-enabled model with suffix:
   - Example: `deepseek-r1:thinking`
   - Or: `claude-3-5-sonnet-20241022:thinking`
3. **Save settings**
4. **Send a test message** that requires reasoning
5. **The thinking widget should appear!** 🎉

## What Changed in the Code

### nanochat/api/client.py (line 286-288)

**Before:**
```python
reasoning = delta.get('reasoning_content')
```

**After:**
```python
# Check multiple possible field names for reasoning content
# NanoGPT uses 'reasoning', OpenAI uses 'reasoning_content'
reasoning = delta.get('reasoning_content') or delta.get('reasoning')
```

This single line change makes the thinking widget compatible with:
- ✅ NanoGPT API (`reasoning` field)
- ✅ OpenAI API (`reasoning_content` field)
- ✅ DeepSeek direct API (`reasoning_content` field)
- ✅ Any other API provider using either format

## Troubleshooting

### Still Not Seeing Thinking Widget?

1. **Check the model name includes `:thinking` suffix**
   ```
   Wrong: deepseek-r1
   Right: deepseek-r1:thinking
   ```

2. **Check logs for reasoning content:**
   ```bash
   python -m nanochat.main 2>&1 | grep -i "reasoning"
   ```

3. **Verify the model supports reasoning:**
   - Not all models have reasoning capability
   - Check NanoGPT's model list for reasoning-capable models

4. **Try with a known reasoning model:**
   ```
   model: deepseek-reasoner:thinking
   ```

## Technical Details

### How NanoGPT Handles Reasoning

NanoGPT provides three endpoint variants:

1. **Default** (`/api/v1/chat/completions`)
   - Streams reasoning in `delta.reasoning`
   - Content in `delta.content`
   - Modern format

2. **Legacy** (`/api/v1legacy/chat/completions`)
   - Streams reasoning in `delta.reasoning_content`
   - For older OpenAI-compatible clients
   - Use if you need the old field name

3. **Thinking** (`/api/v1thinking/chat/completions`)
   - Merges reasoning + content into `delta.content`
   - For clients that ignore reasoning fields
   - Good for simple chat UIs

Your code now works with all three formats! ✅

## Model Suffix Reference

| Suffix | Description | Example |
|--------|-------------|---------|
| `:thinking` | Enable reasoning mode | `deepseek-r1:thinking` |
| `:online` | Enable web search | `gpt-4o:online` |
| `:online/linkup-deep` | Deep web search | `claude:online/linkup-deep` |
| `:memory` | Context memory | `gpt-4o:memory` |
| `:reasoning-exclude` | Hide reasoning from response | `gpt-4o:reasoning-exclude` |

## Sources

- [NanoGPT Chat Completion API](https://docs.nano-gpt.com/api-reference/endpoint/chat-completion)
- [NanoGPT Reasoning Streams Documentation](https://docs.nano-gpt.com/api-reference/endpoint/chat-completion#reasoning-streams)
- [DeepSeek Reasoning Model Guide](https://api-docs.deepseek.com/guides/reasoning_model)
