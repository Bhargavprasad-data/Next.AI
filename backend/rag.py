"""
Simplified RAG implementation with web search capabilities
"""
import os
from typing import List, Optional
import re

from config import settings
from openai import AsyncOpenAI
from web_search import web_search

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)

# Import Gemini support
try:
    import google.generativeai as genai
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class SimpleRAGSystem:
    """Simplified RAG system without vector store dependencies"""
    
    def __init__(self):
        self.documents = []
    
    async def add_documents(self, documents: List[str]) -> List[str]:
        """Add documents to the simple storage"""
        self.documents.extend(documents)
        return [f"doc_{i}" for i in range(len(self.documents))]
    
    async def search_relevant_context(self, query: str, k: int = 3) -> str:
        """Simple keyword-based context search"""
        if not self.documents:
            return ""
        
        # Simple keyword matching
        query_words = query.lower().split()
        scored_docs = []
        
        for doc in self.documents:
            doc_lower = doc.lower()
            score = sum(1 for word in query_words if word in doc_lower)
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = scored_docs[:k]
        
        context = "\n\n".join([doc for _, doc in top_docs])
        return context


# Global RAG instance
rag_system = SimpleRAGSystem()


async def detect_realtime_query(query: str) -> bool:
    """Detect if the query is asking for real-time information"""
    realtime_keywords = [
        'current', 'latest', 'now', 'today', 'recent', 'live', 'real-time',
        'score', 'scores', 'match', 'game', 'news', 'weather', 'stock',
        'price', 'rate', 'exchange rate', 'cryptocurrency', 'bitcoin',
        'election', 'polls', 'results', 'breaking', 'update', 'happening',
        'how is', 'how was', 'ceo', 'ceo of', 'scored', 'runs', 'odi',
        'test match', 't20', 'ipl', 'world cup', 'championship',
        'movie', 'film', 'recipe', 'cooking', 'translate', 'translation',
        'crypto', 'ethereum', 'dogecoin', 'forex', 'currency', 'exchange' ,
        'education', 'study' ,'collage' ,'school' ,'software', 'hardware',
        'health', 'well-being', 'status', 'condition', 'donald trump',
        'trump', 'president', 'biden', 'putin', 'celebrities', 'actor',
        'politician', 'public figure', 'is he', 'is she', 'are they',
        'personal matters', 'private matters', 'wellness', 'health status',
        'doing', 'doing well', 'okay', 'fine', 'doing fine',
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in realtime_keywords)


async def get_realtime_context(query: str) -> str:
    """Get real-time context for queries"""
    try:
        # Detect the type of real-time query
        query_lower = query.lower()
        
        # Check for cryptocurrency queries
        if any(word in query_lower for word in ['bitcoin', 'crypto', 'ethereum', 'dogecoin', 'cryptocurrency']):
            crypto_symbol = 'bitcoin'  # default
            for crypto in ['bitcoin', 'ethereum', 'dogecoin', 'litecoin', 'cardano']:
                if crypto in query_lower:
                    crypto_symbol = crypto
                    break
            return await web_search.get_crypto_prices(crypto_symbol)
        
        # Check for exchange rate queries
        elif any(word in query_lower for word in ['exchange rate', 'forex', 'currency', 'usd to inr', 'eur to usd']):
            from_currency = 'USD'
            to_currency = 'INR'
            if 'usd to inr' in query_lower:
                from_currency, to_currency = 'USD', 'INR'
            elif 'eur to usd' in query_lower:
                from_currency, to_currency = 'EUR', 'USD'
            return await web_search.get_exchange_rates(from_currency, to_currency)
        
        # Check for movie queries
        elif any(word in query_lower for word in ['movie', 'film', 'cinema', 'showtime', 'rating']):
            # Extract movie name (simplified)
            movie_name = query.replace('movie', '').replace('film', '').strip()
            return await web_search.get_movie_info(movie_name)
        
        # Check for recipe queries
        elif any(word in query_lower for word in ['recipe', 'cooking', 'how to cook', 'ingredients']):
            # Extract dish name (simplified)
            dish_name = query.replace('recipe', '').replace('cooking', '').strip()
            return await web_search.get_recipe_info(dish_name)
        
        # Check for translation queries
        elif any(word in query_lower for word in ['translate', 'translation', 'meaning in']):
            return await web_search.get_translation(query)
        
        # Check for celebrity/person queries
        elif any(word in query_lower for word in ['how is', 'how was', 'is he', 'is she', 'are they', 'doing', 'health', 'status', 'condition']):
            # Try to extract the person's name
            person_name = None
            # Common names to check
            common_names = ['dhoni', 'rohit', 'virat', 'sachin', 'kohli', 'sharma', 'trump', 'donald', 'biden', 'putin', 'elon', 'musk']
            for name in common_names:
                if name in query_lower:
                    person_name = name.title()
                    break
            
            # If no specific name found, try to search for any person mentioned
            if not person_name:
                # Try to extract a capitalized word that might be a name
                words = query_lower.split()
                for i, word in enumerate(words):
                    # Check if next word after certain keywords might be a name
                    if word in ['trump', 'biden', 'putin', 'musk', 'bezos', 'gates', 'jobs']:
                        person_name = word.title()
                        break
            
            if person_name:
                return await web_search.get_celebrity_info(person_name)
            else:
                # General person query - try web search
                return await web_search.search_web(query)
        
        # Check for CEO queries
        elif 'ceo' in query_lower and any(company in query_lower for company in ['apple', 'google', 'microsoft', 'amazon', 'tesla', 'meta']):
            # Extract company name
            company_name = None
            for company in ['apple', 'google', 'microsoft', 'amazon', 'tesla', 'meta']:
                if company in query_lower:
                    company_name = company.title()
                    break
            
            if company_name:
                return await web_search.get_company_info(company_name)
        
        # Check for sports queries
        elif any(word in query_lower for word in ['sport', 'score', 'match', 'game', 'team', 'scored', 'runs', 'odi', 'test', 't20', 'ipl']):
            # Extract team/player name
            team_name = None
            for team in ['rohit', 'dhoni', 'virat', 'india', 'pakistan', 'australia', 'england']:
                if team in query_lower:
                    team_name = team.title()
                    break
            
            return await web_search.get_sports_scores(team_name)
        
        elif any(word in query_lower for word in ['news', 'breaking', 'happening']):
            # News query
            return await web_search.get_news()
        
        elif any(word in query_lower for word in ['weather', 'temperature', 'forecast']):
            # Weather query
            location = query_lower
            return await web_search.get_weather_data(location)
        
        else:
            # General real-time query
            results = await web_search.search_web(query)
            if results:
                return f"Current information: {results}"
            else:
                return "I can provide general information about this topic, but for the most current updates, I recommend checking reliable news sources, official websites, or social media."
                
    except Exception as e:
        print(f"Error getting real-time context: {e}")
        return "I can provide general information about this topic, but for the most current updates, I recommend checking reliable news sources, official websites, or social media."


async def get_rag_context(query: str) -> str:
    """Get relevant context for RAG"""
    return await rag_system.search_relevant_context(query)


async def generate_with_rag(
    query: str,
    system_prompt: str = "You are a helpful AI assistant.",
    conversation_history: list = None
) -> str:
    """Generate response using RAG with Gemini as primary and OpenAI as fallback"""
    
    # Check if this is a real-time query
    is_realtime = await detect_realtime_query(query)
    
    # Get context based on query type
    if is_realtime:
        context = await get_realtime_context(query)
    else:
        context = await get_rag_context(query)
    
    # Build enhanced prompt with conversation history
    if context:
        user_prompt = f"""Context (if available):
{context}

User Query: {query}
"""
    else:
        user_prompt = query
    
    # Prepare messages with conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if available
    if conversation_history:
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Add current user message
    messages.append({"role": "user", "content": user_prompt})
    
    # Try Gemini first since it's working
    if GEMINI_AVAILABLE and settings.gemini_api_key:
        try:
            print("Using Gemini as primary AI service...")
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Convert messages to Gemini format
            full_prompt = system_prompt + "\n\n"
            for msg in messages[1:]:  # Skip system message
                if msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    full_prompt += f"Assistant: {msg['content']}\n\n"
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=4000,
                    top_p=0.95,
                )
            )
            print("Gemini response successful!")
            return response.text
            
        except Exception as gemini_error:
            print(f"Gemini failed: {gemini_error}")
            # Fall back to OpenAI
    
    # Try OpenAI as fallback
    try:
        print("Falling back to OpenAI...")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using GPT-3.5-turbo for wider availability
            messages=messages,
            temperature=0.7,  # Balanced creativity and accuracy
            max_tokens=4000,  # Increased for comprehensive responses like ChatGPT/Gemini
            top_p=0.95,       # High quality responses
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        print("OpenAI response successful!")
        return response.choices[0].message.content
        
    except Exception as e:
        error_str = str(e)
        print(f"Error generating response with OpenAI: {e}")
        
        # If both APIs fail, return helpful error message
        if "401" in error_str or "invalid_api_key" in error_str or "api_key" in error_str.lower():
            return """I'm experiencing issues with my AI services right now. This could be due to:

**Possible Solutions:**
1. **API Key Issues**: Check if your OpenAI API key is valid and has sufficient credits
2. **Rate Limits**: You may have exceeded the API rate limits
3. **Service Outage**: The AI services might be temporarily unavailable

**What you can do:**
- Check your OpenAI account billing: https://platform.openai.com/account/billing
- Verify your API key is correct in the .env file
- Try again in a few minutes
- Contact support if the issue persists

I apologize for the inconvenience. Please try again later or check your API configuration."""
        
        return f"I encountered an error: {error_str[:200]}. Please check your API configuration."
