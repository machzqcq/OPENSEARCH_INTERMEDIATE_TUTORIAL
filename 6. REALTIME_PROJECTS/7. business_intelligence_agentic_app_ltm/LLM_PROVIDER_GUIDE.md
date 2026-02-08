# Multi-Provider LLM Configuration Guide

## Overview

The Business Intelligence RAG Application now supports multiple LLM providers, allowing you to choose from:
- **Google Gemini** (gemini-2.0-flash-exp, gemini-2.5-flash, gemini-1.5-pro, etc.)
- **OpenAI GPT** (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, etc.)
- **Anthropic Claude** (claude-3-5-sonnet, claude-3-haiku, etc.)
- **DeepSeek** via OpenRouter (deepseek-chat, deepseek-reasoner, etc.)

## Setup Instructions

### 1. Configure API Keys in `.env` File

Add the API keys for the providers you want to use:

```bash
# Google AI
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# DeepSeek via OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Legacy DeepSeek (optional - for backward compatibility)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**Note**: You only need to configure API keys for the providers you plan to use.

### 2. Start the Application

Run the application:

```bash
python app.py
```

The startup will show which API keys are configured:

```
🚀 Starting Business Intelligence RAG Application
================================================================================
📂 Working Directory: /path/to/project

🔑 Checking API Keys:
  - GOOGLE_API_KEY: ✅
  - OPENAI_API_KEY: ✅
  - ANTHROPIC_API_KEY: ❌
  - OPENROUTER_API_KEY (DeepSeek): ✅
  - DEEPSEEK_API_KEY (Legacy): ❌

💡 Configure LLM provider in the UI (Tab 1) after launch
================================================================================
```

### 3. Configure LLM in the UI

Once the application is running:

1. **Navigate to Tab 1: "Setup & Connect"**
2. **In the "LLM Provider Configuration" section:**
   - Click **"🔍 Load Available Models"** button
   - This will query all configured providers and load available models
3. **Select your provider** from the dropdown (e.g., "google", "openai", "anthropic", "deepseek")
4. **Select your model** from the dropdown (models auto-populate based on provider)
5. **Click "✅ Confirm LLM Selection"**

Example:
```
Provider: google
Model: gemini-2.0-flash-exp
```

## Usage

Once configured, the selected LLM will be used for:
- **Tab 3**: Generating AI descriptions for database columns and tables
- **Tab 6**: Converting natural language questions to SQL queries
- **Tab 9**: Generating business insights from query results

## Provider-Specific Notes

### Google Gemini
- Fast and cost-effective
- Great for general-purpose tasks
- API key format: Starts with `AI...`
- Get key from: https://makersuite.google.com/app/apikey

### OpenAI GPT
- Industry standard for many tasks
- Excellent for complex reasoning
- API key format: Starts with `sk-...`
- Get key from: https://platform.openai.com/api-keys

### Anthropic Claude
- Excellent for long context and detailed analysis
- Great for business insights
- API key format: Starts with `sk-ant-...`
- Get key from: https://console.anthropic.com/

### DeepSeek via OpenRouter
- Cost-effective alternative
- Good reasoning capabilities
- API key is your OpenRouter key
- Get key from: https://openrouter.ai/keys

## Troubleshooting

### "No models available" error
- Check that at least one API key is configured in `.env`
- Verify API keys are valid and have proper permissions
- Check internet connectivity

### "LLM not configured" errors in Tabs 3, 6, or 9
- Make sure you've completed Step 3 above (selected and confirmed LLM)
- Go back to Tab 1 and confirm your selection

### API rate limits or errors
- Switch to a different provider using the UI
- Check your API usage/billing on the provider's dashboard
- Consider using a different model (e.g., smaller/faster models)

## Architecture

The application uses a unified `call_llm()` function that:
1. Reads the selected provider and model from `global_state`
2. Routes the request to the appropriate API client
3. Handles API-specific formatting and error handling
4. Returns a consistent response format

This allows seamless switching between providers without code changes.

## Cost Optimization

For cost-effective usage:
- Use **Google Gemini 2.0 Flash** or **GPT-4o-mini** for metadata enhancement (Tab 3)
- Use more powerful models like **GPT-4o** or **Claude Sonnet** for SQL generation and insights
- Consider using **DeepSeek** via OpenRouter for budget-conscious deployments

## Migration from DeepSeek-Only Version

If you're upgrading from the previous DeepSeek-only version:
- Old configuration still works - just add `OPENROUTER_API_KEY` or `DEEPSEEK_API_KEY`
- All existing functionality is preserved
- You can now add additional providers for flexibility
- No changes needed to existing data or workflows
