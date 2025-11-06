import base64
import os
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


def create_quality_prompt() -> str:
    """Create quality assessment prompt"""
    return """
As a quality control expert, analyze these product images and provide output in this format:

**QUALITY SCORE**: [Score from 0-10]/10

**DEFECTS**:
- [Defect Name]: [MINOR/MAJOR/CRITICAL] - [Location]
(list all defects found)

**VERDICT**: [PASS/FAIL/REWORK]

First image is the PERFECT REFERENCE. Compare the second image against it.
List only deviations and defects found in the second image.
Be precise and concise.
"""


def compare_with_gemini(perfect_bytes: bytes, defective_bytes: bytes) -> Dict:
    """Compare two product images using Gemini Vision"""
    try:
        # Prepare image parts
        image_parts = [
            {"mime_type": "image/jpeg", "data": perfect_bytes},
            {"mime_type": "image/jpeg", "data": defective_bytes}
        ]
        
        # Generate analysis
        prompt = create_quality_prompt()
        response = model.generate_content([prompt, *image_parts])
        
        # Parse the response
        return parse_quality_response(response.text)
        
    except Exception as e:
        return {
            "error": str(e),
            "quality_score": 0,
            "defects": [],
            "recommendation": "ERROR",
            "raw_response": f"Analysis failed: {str(e)}"
        }


def parse_quality_response(content: str) -> Dict:
    """Parse Gemini response into structured data"""
    import re
    
    parsed = {
        "quality_score": 0,
        "defects": [],
        "recommendation": "UNKNOWN",
        "raw_response": content
    }
    
    lines = content.split('\n')
    defect_section = False
    
    for line in lines:
        line = line.strip()
        
        # Extract quality score
        if "QUALITY SCORE" in line.upper():
            score_match = re.search(r'(\d+)/10', line)
            if score_match:
                score = int(score_match.group(1))
                if 0 <= score <= 10:
                    parsed["quality_score"] = score
        
        # Extract verdict/recommendation
        elif "VERDICT" in line.upper() or "RECOMMENDATION" in line.upper():
            if "PASS" in line.upper():
                parsed["recommendation"] = "PASS"
            elif "FAIL" in line.upper():
                parsed["recommendation"] = "FAIL"
            elif "REWORK" in line.upper():
                parsed["recommendation"] = "REWORK"
        
        # Parse defects section
        elif "DEFECTS" in line.upper():
            defect_section = True
            continue
        
        elif defect_section:
            if line.startswith('-') and ':' in line:
                # Parse defect line
                defect_text = line[1:].strip()
                try:
                    parts = defect_text.split(':')
                    if len(parts) >= 2:
                        defect_name = parts[0].strip()
                        rest = ':'.join(parts[1:]).strip()
                        
                        # Try to extract severity and location
                        if '-' in rest:
                            severity_part, location_part = rest.split('-', 1)
                            severity = severity_part.strip().upper()
                            location = location_part.strip()
                        else:
                            severity = "UNKNOWN"
                            location = rest
                        
                        parsed["defects"].append({
                            "name": defect_name,
                            "severity": severity,
                            "location": location
                        })
                except:
                    continue
            elif line.startswith('**'):
                defect_section = False
    
    return parsed