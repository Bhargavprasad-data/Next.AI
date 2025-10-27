"""
Enhanced web search functionality with multiple APIs for real-time information
"""
import requests
import json
from typing import Optional, Dict, Any
from config import settings
import asyncio
import aiohttp

class WebSearchService:
    """Service for fetching real-time information from multiple APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def search_web(self, query: str, num_results: int = 3) -> str:
        """Search the web for current information using multiple sources"""
        try:
            # Try multiple search sources
            results = await self._search_multiple_sources(query)
            
            # Return formatted context
            if results.get('abstract') or results.get('abstract_text'):
                abstract = results.get('abstract') or results.get('abstract_text', '')
                answer = results.get('answer', '')
                if answer:
                    return f"{abstract}\n\n{answer}"
                return abstract
            elif results.get('definition'):
                return results.get('definition', '')
            elif results.get('wikipedia'):
                wiki = results.get('wikipedia', {})
                if wiki.get('summary'):
                    return wiki.get('summary', '')
            
            return ""
            
        except Exception as e:
            print(f"Web search error: {e}")
            return ""
    
    async def _search_multiple_sources(self, query: str) -> Dict[str, Any]:
        """Search multiple sources for better results"""
        results = {}
        
        # Try DuckDuckGo first
        try:
            ddg_results = await self._search_duckduckgo(query)
            if ddg_results.get('abstract'):
                results.update(ddg_results)
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        # Try Wikipedia for additional context
        try:
            wiki_results = await self._search_wikipedia(query)
            if wiki_results.get('summary'):
                results['wikipedia'] = wiki_results
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        # Try News API if available
        try:
            news_results = await self._search_news_api(query)
            if news_results.get('articles'):
                results['news'] = news_results
        except Exception as e:
            print(f"News API search error: {e}")
        
        return results
    
    async def _search_duckduckgo(self, query: str) -> Dict[str, Any]:
        """Search DuckDuckGo for information"""
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'abstract': data.get('Abstract', ''),
            'abstract_text': data.get('AbstractText', ''),
            'definition': data.get('Definition', ''),
            'answer': data.get('Answer', ''),
            'related_topics': data.get('RelatedTopics', [])[:3],
            'infobox': data.get('Infobox', {}),
            'type': data.get('Type', ''),
            'heading': data.get('Heading', ''),
            'url': data.get('AbstractURL', ''),
            'image': data.get('Image', '')
        }
    
    async def _search_wikipedia(self, query: str) -> Dict[str, Any]:
        """Search Wikipedia for additional context"""
        try:
            # Wikipedia API
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            search_query = query.replace(' ', '_')
            
            response = self.session.get(f"{url}{search_query}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'summary': data.get('extract', ''),
                    'title': data.get('title', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'thumbnail': data.get('thumbnail', {}).get('source', '') if data.get('thumbnail') else ''
                }
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        return {}
    
    async def _search_news_api(self, query: str) -> Dict[str, Any]:
        """Search News API for current news (if API key available)"""
        # Note: This would require a News API key
        # For now, return empty results
        return {}
    
    async def get_crypto_prices(self, symbol: str = "bitcoin") -> str:
        """Get cryptocurrency prices"""
        try:
            # Use CoinGecko API (free, no API key required)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': symbol.lower(),
                'vs_currencies': 'usd,eur,inr',
                'include_24hr_change': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if symbol.lower() in data:
                            price_data = data[symbol.lower()]
                            return f"""**{symbol.upper()} Current Price:**
- **USD**: ${price_data.get('usd', 'N/A')}
- **EUR**: €{price_data.get('eur', 'N/A')}
- **INR**: ₹{price_data.get('inr', 'N/A')}
- **24h Change**: {price_data.get('usd_24h_change', 'N/A')}%

For the most current prices, check CoinGecko, CoinMarketCap, or Binance."""
            
            return f"I can provide general information about {symbol}, but for the most current cryptocurrency prices, check CoinGecko, CoinMarketCap, or Binance."
            
        except Exception as e:
            return f"I can help you with general information about {symbol}, but for current cryptocurrency prices, check CoinGecko, CoinMarketCap, or Binance."
    
    async def get_stock_prices(self, symbol: str) -> str:
        """Get stock prices"""
        try:
            # Use Alpha Vantage API (free tier available)
            # Note: This would require an API key
            return f"I can provide general information about {symbol} stock, but for the most current stock prices, check Yahoo Finance, Google Finance, or Bloomberg."
            
        except Exception as e:
            return f"I can help you with general information about {symbol}, but for current stock prices, check Yahoo Finance, Google Finance, or Bloomberg."
    
    async def get_weather_data(self, location: str) -> str:
        """Get weather information"""
        try:
            # Use OpenWeatherMap API (free tier available)
            # Note: This would require an API key
            return f"I can provide general weather information about {location}, but for current weather conditions, check Weather.com, BBC Weather, or your local weather service."
            
        except Exception as e:
            return f"I can help you with general weather information about {location}, but for current conditions, check Weather.com, BBC Weather, or your local weather service."
    
    async def get_exchange_rates(self, from_currency: str = "USD", to_currency: str = "INR") -> str:
        """Get currency exchange rates"""
        try:
            # Use ExchangeRate-API (free tier available)
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate = data.get('rates', {}).get(to_currency.upper(), 'N/A')
                        return f"""**{from_currency.upper()} to {to_currency.upper()} Exchange Rate:**
- **Current Rate**: 1 {from_currency.upper()} = {rate} {to_currency.upper()}
- **Last Updated**: {data.get('date', 'N/A')}

For the most current exchange rates, check XE.com, OANDA, or your bank's website."""
            
            return f"I can provide general information about {from_currency} to {to_currency} exchange rates, but for current rates, check XE.com, OANDA, or your bank's website."
            
        except Exception as e:
            return f"I can help you with general information about currency exchange rates, but for current rates, check XE.com, OANDA, or your bank's website."
    
    async def get_movie_info(self, movie_name: str) -> str:
        """Get movie information"""
        try:
            # Use OMDB API (free tier available)
            # Note: This would require an API key
            return f"I can provide general information about the movie '{movie_name}', but for current ratings, showtimes, and reviews, check IMDb, Rotten Tomatoes, or your local cinema websites."
            
        except Exception as e:
            return f"I can help you with general information about movies, but for current ratings and showtimes, check IMDb, Rotten Tomatoes, or cinema websites."
    
    async def get_recipe_info(self, dish_name: str) -> str:
        """Get recipe information"""
        try:
            # Use Edamam Recipe API (free tier available)
            # Note: This would require an API key
            return f"I can provide general cooking information about '{dish_name}', but for detailed recipes, check AllRecipes, Food Network, or BBC Good Food."
            
        except Exception as e:
            return f"I can help you with general cooking information, but for detailed recipes, check AllRecipes, Food Network, or BBC Good Food."
    
    async def get_translation(self, text: str, from_lang: str = "auto", to_lang: str = "en") -> str:
        """Get translation"""
        try:
            # Use Google Translate API (free tier available)
            # Note: This would require an API key
            return f"I can help you with general language information, but for accurate translations, check Google Translate, DeepL, or Microsoft Translator."
            
        except Exception as e:
            return f"I can help you with general language information, but for accurate translations, check Google Translate, DeepL, or Microsoft Translator."
    
    async def get_celebrity_info(self, name: str) -> str:
        """Get current information about celebrities"""
        try:
            query = f"{name} latest news current status"
            results = await self.search_web(query)
            
            if results:
                return f"Here's what I found about {name}:\n\n{results}\n\nFor the most current information, check their official social media, Wikipedia, or news sources like BBC, CNN, or Google News."
            else:
                return f"I can provide general information about {name}, but for the most current updates, I recommend checking their official social media accounts, Wikipedia, or news sources like BBC News, CNN, or Google News."
                
        except Exception as e:
            return f"I can help you with general information about {name}, but for the latest updates, check their official social media, Wikipedia, or news websites."
    
    async def get_company_info(self, company: str) -> str:
        """Get current information about companies"""
        try:
            query = f"{company} CEO current leadership latest news"
            results = await self.search_web(query)
            
            if results:
                return f"Here's what I found about {company}:\n\n{results}\n\nFor the most current information about {company}'s leadership and news, check their official website, Wikipedia, or business news sources like Bloomberg, Reuters, or CNBC."
            else:
                return f"I can provide general information about {company}, but for the most current updates about their leadership and business news, I recommend checking their official website, Wikipedia, or business news sources like Bloomberg, Reuters, or CNBC."
                
        except Exception as e:
            return f"I can help you with general information about {company}, but for the latest updates, check their official website or business news sources."
    
    async def get_sports_scores(self, team: str = None, league: str = None) -> str:
        """Get current sports information"""
        try:
            if team:
                query = f"{team} latest scores results recent matches"
            elif league:
                query = f"{league} latest scores results recent matches"
            else:
                query = "latest sports scores results"
            
            results = await self.search_web(query)
            
            if results:
                return f"Here's what I found:\n\n{results}\n\nFor the most current scores and match results, I recommend checking ESPN, BBC Sport, Cricbuzz (for cricket), or your team's official website."
            else:
                return f"I can provide general information about {team or league or 'sports'}, but for the most current scores and match results, I recommend checking ESPN, BBC Sport, Cricbuzz (for cricket), or official team websites."
                
        except Exception as e:
            return f"I can help you with general information about {team or league or 'sports'}, but for current scores, please check ESPN, BBC Sport, Cricbuzz (for cricket), or official team websites."
    
    async def get_news(self, topic: str = None) -> str:
        """Get current news information"""
        try:
            query = f"latest news {topic}" if topic else "latest news"
            results = await self.search_web(query)
            
            if results:
                return f"Here's what I found about {query}:\n\n{results}\n\nFor the most current news, I recommend checking BBC News, CNN, Reuters, or Google News."
            else:
                return f"I don't have access to real-time news, but I can help you understand {topic or 'current events'} in general. For the latest news, check BBC News, CNN, Reuters, or Google News."
                
        except Exception as e:
            return f"I can't access real-time news right now. For current news, please check BBC News, CNN, Reuters, or Google News."
    
    async def get_weather(self, location: str) -> str:
        """Get weather information"""
        try:
            query = f"weather {location} current conditions"
            results = await self.search_web(query)
            
            if results:
                return f"Here's what I found about weather in {location}:\n\n{results}\n\nFor the most current weather, I recommend checking Weather.com, BBC Weather, or your local weather service."
            else:
                return f"I don't have access to real-time weather data, but I can help you understand weather patterns in {location}. For current conditions, check Weather.com, BBC Weather, or your local weather service."
                
        except Exception as e:
            return f"I can't access real-time weather data right now. For current weather, please check Weather.com, BBC Weather, or your local weather service."

# Global web search instance
web_search = WebSearchService()
