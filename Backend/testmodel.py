import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

print("Testing Gemini API connection...")
print(f"API Key configured: {bool(GOOGLE_API_KEY)}")

try:
    # List available models
    print("\nAvailable models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  - {m.name}")
    
    # Test the specific model
    print("\nTesting gemini-1.5-flash...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say hello")
    print(f"✅ Success! Response: {response.text[:50]}")
    
except Exception as e:
    print(f"❌ Error: {e}")