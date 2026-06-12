import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class RateLimitError(Exception):
    """Raised when the LLM provider returns a 429 Too Many Requests"""
    pass

class LLMService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            # cls._instance.model = "llama-3.3-70b-versatile"
            cls._instance.model = "llama-3.1-8b-instant"
            
        return cls._instance

    def get_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Fetch a structured JSON response from the LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Check for rate limit error
            if "rate_limit_exceeded" in str(e).lower() or "429" in str(e):
                print(f"      [LLM Service] Rate limit hit.")
                print(e)
                raise RateLimitError("AI daily limit reached. Please try again later.")
            
            print(f"      [LLM Service Error] {e}")
            return None
