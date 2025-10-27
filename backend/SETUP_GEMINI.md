# Setting Up Gemini API

## Step 1: Get Your Gemini API Key

1. Go to Google AI Studio: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

## Step 2: Update Configuration

Edit `backend/env.txt` and replace:
```
GEMINI_API_KEY=AIzaSyCPcZi0U0IoVYLFlfQSkS_TAFROL6P2Inc
```

With your actual key:
```
GEMINI_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY
```

## Step 3: Install Gemini Support

```bash
pip install google-generativeai langchain-google-genai
```

## Step 4: Restart Backend

Restart your backend server to load the new API key.

## Using Gemini

The application currently uses OpenAI GPT-3.5-turbo by default. You can modify `backend/rag.py` to use Gemini if desired.


