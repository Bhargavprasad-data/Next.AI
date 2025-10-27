"""
Google Gemini AI integration
"""
try:
    import google.generativeai as genai
    from config import settings
    
    # Initialize Gemini client
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
    
    def generate_gemini_response(prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        """Generate response using Google Gemini"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error with Gemini: {str(e)}"
    
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    
    def generate_gemini_response(prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        return "Gemini support not installed. Please run: pip install google-generativeai"


