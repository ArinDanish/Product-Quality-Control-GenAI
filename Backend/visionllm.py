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
model = genai.GenerativeModel("gemini-2.0-flash-exp")


def create_quality_prompt() -> str:
    """Create quality assessment prompt for single image comparison"""
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


def create_multi_angle_prompt() -> str:
    """Create quality assessment prompt for multi-angle comparison"""
    return """
As a quality control expert, analyze these product images from multiple angles and provide output in this format:

**OVERALL QUALITY SCORE**: [Score from 0-10]/10

**FRONT VIEW ANALYSIS**:
Quality Score: [0-10]/10
Defects:
- [Defect Name]: [MINOR/MAJOR/CRITICAL] - [Location]

**BACK VIEW ANALYSIS**:
Quality Score: [0-10]/10
Defects:
- [Defect Name]: [MINOR/MAJOR/CRITICAL] - [Location]

**LEFT VIEW ANALYSIS**:
Quality Score: [0-10]/10
Defects:
- [Defect Name]: [MINOR/MAJOR/CRITICAL] - [Location]

**RIGHT VIEW ANALYSIS**:
Quality Score: [0-10]/10
Defects:
- [Defect Name]: [MINOR/MAJOR/CRITICAL] - [Location]

**ALL DEFECTS SUMMARY**:
- [Defect Name]: [MINOR/MAJOR/CRITICAL] - [Location and View]

**OVERALL VERDICT**: [PASS/FAIL/REWORK]

Images are provided in pairs (perfect reference, test sample) for each angle: Front, Back, Left, Right.
Compare each test sample angle against its corresponding perfect reference.
Front should be compared with front, back with back, left with left, right with right.
Provide detailed analysis for each angle and an overall assessment.
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


def compare_multi_angle_with_gemini(
    perfect_front: bytes,
    perfect_back: bytes,
    perfect_left: bytes,
    perfect_right: bytes,
    defective_front: bytes,
    defective_back: bytes,
    defective_left: bytes,
    defective_right: bytes
) -> Dict:
    """Compare product images from multiple angles using Gemini Vision"""
    try:
        # Prepare image parts in order: perfect_front, defective_front, perfect_back, defective_back, etc.
        image_parts = [
            {"mime_type": "image/jpeg", "data": perfect_front},
            {"mime_type": "image/jpeg", "data": defective_front},
            {"mime_type": "image/jpeg", "data": perfect_back},
            {"mime_type": "image/jpeg", "data": defective_back},
            {"mime_type": "image/jpeg", "data": perfect_left},
            {"mime_type": "image/jpeg", "data": defective_left},
            {"mime_type": "image/jpeg", "data": perfect_right},
            {"mime_type": "image/jpeg", "data": defective_right}
        ]
        
        # Generate analysis
        prompt = create_multi_angle_prompt()
        response = model.generate_content([prompt, *image_parts])
        
        # Parse the response
        return parse_multi_angle_response(response.text)
        
    except Exception as e:
        return {
            "error": str(e),
            "overall_score": 0,
            "angle_results": {},
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
        elif "DEFECTS" in line.upper() and "ALL DEFECTS" not in line.upper():
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


def parse_multi_angle_response(content: str) -> Dict:
    """Parse multi-angle Gemini response into structured data"""
    import re
    
    parsed = {
        "overall_score": 0,
        "angle_results": {
            "front": {"quality_score": 0, "defects": []},
            "back": {"quality_score": 0, "defects": []},
            "left": {"quality_score": 0, "defects": []},
            "right": {"quality_score": 0, "defects": []}
        },
        "defects": [],
        "recommendation": "UNKNOWN",
        "raw_response": content
    }
    
    lines = content.split('\n')
    current_angle = None
    defect_section = False
    all_defects_section = False
    
    for line in lines:
        line = line.strip()
        
        # Extract overall quality score
        if "OVERALL QUALITY SCORE" in line.upper():
            score_match = re.search(r'(\d+)/10', line)
            if score_match:
                score = int(score_match.group(1))
                if 0 <= score <= 10:
                    parsed["overall_score"] = score
        
        # Detect angle sections
        elif "FRONT VIEW" in line.upper():
            current_angle = "front"
            defect_section = False
        elif "BACK VIEW" in line.upper():
            current_angle = "back"
            defect_section = False
        elif "LEFT VIEW" in line.upper():
            current_angle = "left"
            defect_section = False
        elif "RIGHT VIEW" in line.upper():
            current_angle = "right"
            defect_section = False
        
        # Extract angle-specific quality score
        elif current_angle and "QUALITY SCORE" in line.upper() and "OVERALL" not in line.upper():
            score_match = re.search(r'(\d+)/10', line)
            if score_match:
                score = int(score_match.group(1))
                if 0 <= score <= 10:
                    parsed["angle_results"][current_angle]["quality_score"] = score
        
        # Detect defects section for current angle
        elif current_angle and "DEFECTS" in line.upper() and "ALL DEFECTS" not in line.upper():
            defect_section = True
            continue
        
        # Detect all defects summary section
        elif "ALL DEFECTS SUMMARY" in line.upper():
            all_defects_section = True
            defect_section = False
            current_angle = None
            continue
        
        # Extract verdict
        elif "OVERALL VERDICT" in line.upper() or "VERDICT" in line.upper():
            if "PASS" in line.upper():
                parsed["recommendation"] = "PASS"
            elif "FAIL" in line.upper():
                parsed["recommendation"] = "FAIL"
            elif "REWORK" in line.upper():
                parsed["recommendation"] = "REWORK"
        
        # Parse defects for current angle
        elif defect_section and current_angle and line.startswith('-') and ':' in line:
            defect_text = line[1:].strip()
            try:
                parts = defect_text.split(':')
                if len(parts) >= 2:
                    defect_name = parts[0].strip()
                    rest = ':'.join(parts[1:]).strip()
                    
                    if '-' in rest:
                        severity_part, location_part = rest.split('-', 1)
                        severity = severity_part.strip().upper()
                        location = location_part.strip()
                    else:
                        severity = "UNKNOWN"
                        location = rest
                    
                    parsed["angle_results"][current_angle]["defects"].append({
                        "name": defect_name,
                        "severity": severity,
                        "location": location
                    })
            except:
                continue
        
        # Parse all defects summary
        elif all_defects_section and line.startswith('-') and ':' in line:
            defect_text = line[1:].strip()
            try:
                parts = defect_text.split(':')
                if len(parts) >= 2:
                    defect_name = parts[0].strip()
                    rest = ':'.join(parts[1:]).strip()
                    
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
            if "ALL DEFECTS" not in line.upper():
                all_defects_section = False
    
    return parsed