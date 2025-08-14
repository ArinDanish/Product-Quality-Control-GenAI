import base64
import requests
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import os
from PIL import Image, ImageDraw, ImageFont

# Load environment variables first
load_dotenv()

# Configure Gemini with API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# Debug: Print if API key is loaded
print(f"Google API Key loaded: {'Yes' if GOOGLE_API_KEY else 'No'}")

# Usage Example
def main():
    print("Starting Quality Control Analysis...")
    
    # Initialize the quality controller
    qc = VisionQualityController(api_key=os.getenv("GOOGLE_API_KEY"), model_provider="google")
    
    # Check for test images in the current directory first
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_images = []
    
    # Look for any jpg or jpeg files in the current directory
    for file in os.listdir(current_dir):
        if file.lower().endswith(('.jpg', '.jpeg')):
            test_images.append(os.path.join(current_dir, file))
    
    if not test_images:
        print("\nNo test images found!")
        print("===================")
        print("To use this script:")
        print("1. Place some .jpg or .jpeg images in this directory:")
        print(f"   {current_dir}")
        print("2. The first image will be used as the reference (perfect sample)")
        print("3. All other images will be compared against the reference")
        print("\nExample file names:")
        print("- perfect_sample.jpg (will be used as reference)")
        print("- test_item_1.jpg")
        print("- test_item_2.jpg")
        return
    
    # Use the first image as reference and analyze the rest
    reference_image = test_images[0]
    print(f"Using {os.path.basename(reference_image)} as reference image")
    
    # Create a simple batch analysis with found images
    products = {}
    for i, img_path in enumerate(test_images[1:], 1):
        product_id = f"product_{i:03d}"
        products[product_id] = [img_path]
        print(f"Added {os.path.basename(img_path)} for analysis")
    
    # Only proceed with batch analysis if we have products to analyze
    if products:
        print("\nStarting batch analysis...")
        batch_results = qc.analyze_batch_products(products, reference_image=reference_image)
        
        for product_id, analysis in batch_results.items():
            print(f"\n=== {product_id} ===")
            print(f"Score: {analysis.get('quality_score', 'N/A')}/10")
            print(f"Recommendation: {analysis.get('recommendation', 'N/A')}")
    else:
        print("No additional images found for comparison with the reference image.")
# Configure Gemini model
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')
# gemini-1.5-pro-002

# Debug: Print if API key is loaded
print(f"Google API Key loaded: {'Yes' if GOOGLE_API_KEY else 'No'}")


class VisionQualityController:
    def __init__(self, api_key: str = None, model_provider: str = "google"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided and GOOGLE_API_KEY not found in environment")
        self.model_provider = model_provider
        
        # API endpoints
        self.endpoints = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "google": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
        }
        
    def encode_image(self, image_path: str) -> str:
        """Convert image to base64 for API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_quality_prompt(self, product_type: str = "handcrafted item") -> str:
        """Create concise quality assessment prompt"""
        return f"""
        As a quality control expert, analyze this {product_type} and provide a concise output in exactly this format:

        **QUALITY SCORE**: [Enter a score from 0-10]/10

        **DEFECTS**:
        - [Defect]: [MINOR/MAJOR/CRITICAL] - [Location]
        - [Defect]: [MINOR/MAJOR/CRITICAL] - [Location]
        (list all defects found)

        **VERDICT**: [PASS/FAIL/REWORK]

        Keep responses brief and focused only on defects found. Do not include explanations or detailed analysis.
        """
    
    def analyze_with_gemini(self, image_paths: List[str], custom_prompt: str = None) -> Dict:
        """Analyze images using Google's Gemini 1.5 Pro Vision"""
        try:
            # Create a list to store image parts
            image_parts = []
            
            # Load all images
            for img_path in image_paths:
                with open(img_path, 'rb') as img_file:
                    image_data = img_file.read()
                    image_parts.append({"mime_type": "image/jpeg", "data": image_data})
            
            # Generate content using Gemini
            prompt = custom_prompt or self.create_quality_prompt()
            response = model.generate_content([prompt, *image_parts])
            
            # Format response to match expected structure
            return {
                "choices": [{
                    "message": {
                        "content": response.text
                    }
                }]
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze with Gemini: {str(e)}"}
    
    def analyze_batch_products(self, product_images: Dict[str, List[str]], 
                             reference_image: str = None) -> Dict[str, Dict]:
        """Analyze multiple products against reference or standards"""
        results = {}
        
        for product_id, images in product_images.items():
            try:
                # Include reference image if provided
                analysis_images = images.copy()
                if reference_image:
                    analysis_images.insert(0, reference_image)
                    
                    prompt = f"""
                    REFERENCE COMPARISON ANALYSIS:
                    The first image is the PERFECT REFERENCE standard.
                    Compare subsequent images against this reference for quality assessment.
                    
                    {self.create_quality_prompt()}
                    
                    Focus on deviations from the reference standard.
                    """
                else:
                    prompt = self.create_quality_prompt()
                
                result = self.analyze_with_gemini(analysis_images, prompt)
                results[product_id] = self.parse_quality_response(result)
                
            except Exception as e:
                results[product_id] = {"error": str(e)}
        
        return results
    
    def parse_quality_response(self, response: Dict) -> Dict:
        """Parse and structure the quality analysis response"""
        try:
            # Handle Gemini response format
            if isinstance(response, dict) and 'text' in response:
                content = response['text']
            elif isinstance(response, dict) and 'choices' in response:
                content = response['choices'][0]['message']['content']
            else:
                content = str(response)
            
            # Clean the response
            cleaned_content = content.replace('\\n', '\n').replace('\\"', '"')
            
            # Extract key metrics (basic parsing - can be enhanced)
            lines = content.split('\n')
            parsed = {
                "raw_response": cleaned_content,
                "quality_score": None,
                "defects": [],
                "recommendation": None,
                "analysis_timestamp": None
            }
            
            defect_section = False
            for line in lines:
                line = line.strip()
                if "DEFECTS" in line.upper():
                    defect_section = True
                    continue
                elif defect_section and line.startswith('-') and ':' in line:
                    # Parse defect line
                    defect_info = line[1:].strip()  # Remove the leading -
                    try:
                        defect_name, rest = defect_info.split(':', 1)
                        severity, location = rest.strip().split('-', 1)
                        parsed["defects"].append({
                            "name": defect_name.strip(),
                            "severity": severity.strip().upper(),
                            "location": location.strip()
                        })
                    except ValueError:
                        continue  # Skip malformed defect lines
                elif line.startswith('**') and not line.startswith('**DEFECTS'):
                    defect_section = False  # End of defects section
            
            for line in lines:
                if "QUALITY SCORE" in line.upper():
                    # Extract score using regex to find X/10 pattern
                    import re
                    score_match = re.search(r'(\d+)/10', line)
                    if score_match:
                        score = score_match.group(1)
                        # Validate score is between 0 and 10
                        score_num = int(score)
                        if 0 <= score_num <= 10:
                            parsed["quality_score"] = score_num
                
                elif "VERDICT" in line.upper() or "RECOMMENDATION" in line.upper():
                    if "PASS" in line.upper():
                        parsed["recommendation"] = "PASS"
                    elif "FAIL" in line.upper():
                        parsed["recommendation"] = "FAIL"
                    elif "REWORK" in line.upper():
                        parsed["recommendation"] = "REWORK"
            
            return parsed
            
        except Exception as e:
            return {"error": f"Failed to parse response: {str(e)}"}
    
    def mark_defects_on_image(self, image_path: str, defects: List[Dict]) -> Image.Image:
        """Mark defects on the image with annotations"""
        # Open the image
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # Define colors for different severity levels
        severity_colors = {
            "MINOR": "#FFE135",    # Yellow
            "MAJOR": "#FFA500",    # Orange
            "CRITICAL": "#FF0000"  # Red
        }
        
        # Calculate text size based on image dimensions
        font_size = int(min(image.size) * 0.03)  # 3% of the smaller dimension
        try:
            # Try to use a system font, fallback to default if not available
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Add legend
        legend_y = 10
        for severity, color in severity_colors.items():
            draw.rectangle([10, legend_y, 30, legend_y + 20], fill=color)
            draw.text((35, legend_y), severity, fill="white", font=font)
            legend_y += 25

        # Mark each defect
        for i, defect in enumerate(defects, 1):
            severity = defect.get("severity", "MINOR")
            location = defect.get("location", "").lower()
            color = severity_colors.get(severity, "#FFFFFF")
            
            # Simple position mapping (can be enhanced with more specific location parsing)
            x, y = self._get_position_from_location(location, image.size)
            
            # Draw a circle and number
            circle_radius = int(min(image.size) * 0.03)
            draw.ellipse([x - circle_radius, y - circle_radius, 
                         x + circle_radius, y + circle_radius], 
                         outline=color, width=3)
            
            # Add defect number and description
            text = f"{i}. {defect.get('name', '')}"
            draw.text((x + circle_radius + 5, y - font_size//2), 
                     text, fill=color, font=font)
        
        return image
    
    def _get_position_from_location(self, location: str, image_size: Tuple[int, int]) -> Tuple[int, int]:
        """Convert location description to x,y coordinates"""
        width, height = image_size
        x, y = width // 2, height // 2  # Default to center
        
        # Basic position mapping
        if "top" in location:
            y = height // 4
        if "bottom" in location:
            y = (height * 3) // 4
        if "left" in location:
            x = width // 4
        if "right" in location:
            x = (width * 3) // 4
        if "center" in location:
            x, y = width // 2, height // 2
            
        return x, y

    def comparative_analysis(self, perfect_image: str, test_image: str, 
                           product_type: str = "handcrafted item") -> Dict:
        """Direct comparison between perfect and test samples"""
        
        prompt = f"""
        Compare these two {product_type} images and provide output in exactly this format:

        **QUALITY SCORE**: [Score]/10

        **DEFECTS**:
        - [Defect]: [MINOR/MAJOR/CRITICAL] - [Location]
        - [Defect]: [MINOR/MAJOR/CRITICAL] - [Location]
        (list all differences from perfect sample)

        **VERDICT**: [PASS/FAIL/REWORK]

        First image is the perfect reference. List only deviations found in second image. Be concise, no explanations needed.
        """
        
        result = self.analyze_with_gemini([perfect_image, test_image], prompt)
        return self.parse_quality_response(result)

# Usage Example
def main():
    print("\nStarting Quality Control Analysis...")
    print("====================================")
    
    # Initialize the quality controller
    qc = VisionQualityController(api_key=os.getenv("GOOGLE_API_KEY"), model_provider="google")
    
    # Define image paths
    perfect_sample = r"D:\Product-Quality-Control-GenAI\Images\perfect.jpeg"
    test_sample = r"D:\Product-Quality-Control-GenAI\Images\defect2.jpeg"
    
    # Validate image paths
    if not os.path.exists(perfect_sample):
        print(f"Error: Perfect sample image not found at: {perfect_sample}")
        return
    if not os.path.exists(test_sample):
        print(f"Error: Test sample image not found at: {test_sample}")
        return
        
    print(f"\nAnalyzing images:")
    print(f"Reference image: {os.path.basename(perfect_sample)}")
    print(f"Test image: {os.path.basename(test_sample)}")
    print("\nProcessing comparison...")
    
    # Perform the comparison analysis
    result = qc.comparative_analysis(perfect_sample, test_sample, "product")
    
    print("\nQuality Analysis Result:")
    print("=====================")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()