# Fix for Accurate and Correct Answers

## Problem
The AI was giving wrong answers to user queries. Users need accurate, factually correct information.

## Solution Applied

### Enhanced System Prompts with Accuracy Guidelines

Added **ACCURACY IS PARAMOUNT** section to both system prompts (main chat and file-based chat) in `backend/main.py`.

### New Accuracy Requirements:

**ACCURACY IS PARAMOUNT:**
- ✅ Only provide information you are certain is correct
- ✅ Fact-check information before including it in your response
- ✅ If you're uncertain about facts, clearly indicate what is confirmed vs. what is less certain
- ✅ Do not make up information or guess
- ✅ If you don't know something, say what you do know and suggest where to find accurate information
- ✅ Cross-reference information when possible
- ✅ Be precise with names, dates, places, and figures
- ✅ Distinguish between confirmed facts and widely reported information that may need verification

### Structure and Delivery:

1. **Understand the user question carefully.**
2. **Provide concise, accurate answers** structured with bullet points or sections if needed.
3. **Remain neutral** - no speculation or personal opinions.
4. **Include relevant categories/topics** (e.g., for a person: public appearances, career, legal matters, media presence).
5. **Add timestamps** when information can change (e.g., "as of October 2025").
6. **Suggest reliable sources** for verification (official websites, Wikipedia, reputable news organizations).
7. **Professional but readable tone** - friendly when appropriate.

## What This Fixes

### Before:
- AI might provide unverified or incorrect information
- No emphasis on fact-checking
- Guessing when uncertain
- Mixing confirmed facts with unconfirmed information

### After:
- AI prioritizes accuracy above all else
- Fact-checks information before providing it
- Clearly distinguishes between confirmed and uncertain information
- Does not make up or guess at information
- Provides sources for verification
- Precise with details like names, dates, places

## Expected Behavior

When users ask questions, the AI will now:

1. ✅ **Fact-check** information before responding
2. ✅ **Only provide** information it's certain about
3. ✅ **Clearly indicate** uncertainty when facts are uncertain
4. ✅ **Never guess** or make up information
5. ✅ **Cross-reference** information when possible
6. ✅ **Be precise** with names, dates, places, and figures
7. ✅ **Distinguish** between confirmed facts and widely-reported information
8. ✅ **Suggest sources** for verification

## Testing

Test by asking questions that require factual accuracy:
- "What is the capital of France?"
- "When was World War II?"
- "Who is the current president of the United States?"
- "What is 2 + 2?"

The AI should now:
- Provide only correct, verified information
- Include sources for verification when appropriate
- Indicate uncertainty when facts aren't confirmed
- Never guess or make up information

