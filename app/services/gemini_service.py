import google.generativeai as genai # type: ignore
from app.config import settings
from fastapi import HTTPException, status # type: ignore    
import os
from PIL import Image # type: ignore

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiService:
    def __init__(self):
        # Use most stable working models for free tier
        # gemini-1.5-flash-latest is the current working free model
        self.text_model = genai.GenerativeModel('gemini-2.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_text_response(self, message: str) -> str:
        """
        Generate response for text message - Optimized for speed
        Supports English and Roman Urdu
        """
        try:
            # Simple direct prompt
            prompt = f"""You must reply in the SAME language/script the user uses. If user writes in Roman Urdu (Urdu words in English letters like 'kasay ho'), reply ONLY in Roman Urdu. If English, reply in English."""
            prompt += f"\nUser: {message}"
            
            
            # Optimized config with higher token limit
            generation_config = {
                "temperature": 1.0,
                "max_output_tokens": 2048,  # Higher limit for complete responses
                "top_p": 0.95,
                "top_k": 64
            }
            
            # Safety settings - Allow most content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            response = self.text_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if not response or not response.text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate response from AI"
                )
            
            return response.text
        
        except Exception as e:
            print(f"Error generating text response: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate AI response: {str(e)}"
            )
    
    async def generate_image_response(self, message: str, image_path: str) -> str:
        """
        Generate response for image with text prompt - Optimized
        """
        image = None  # Initialize to None
        try:
            # Open and validate image
            if not os.path.exists(image_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image file not found"
                )
            
            # Open image
            image = Image.open(image_path)
            
            # Simple direct prompt
            prompt = message
            
            # Optimized config with higher token limit
            generation_config = {
                "temperature": 1.0,
                "max_output_tokens": 2048,
                "top_p": 0.95,
                "top_k": 64
            }
            
            # Safety settings - Allow most content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Generate response with image
            response = self.vision_model.generate_content(
                [prompt, image],
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # IMPORTANT: Close image file immediately after use
            if image:
                image.close()
            
            if not response or not response.text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate response from AI"
                )
            
            return response.text
        
        except Exception as e:
            # Make sure to close image on error too
            if image:
                try:
                    image.close()
                except:
                    pass  # Ignore close errors
            
            print(f"Error generating image response: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate AI response for image: {str(e)}"
            )
    
    def validate_and_process_message(self, message: str) -> str:
        """
        Validate and process user message
        """
        if not message or len(message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Limit message length
        if len(message) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is too long. Maximum 5000 characters allowed."
            )
        
        return message.strip()


# Create singleton instance
gemini_service = GeminiService()

