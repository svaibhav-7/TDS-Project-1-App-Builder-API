import os
import json
import logging
from typing import Dict, List, Optional, Any
import openai
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL
        # Only initialize the client if an API key is provided
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client, will fallback: {e}")
                self.client = None
        else:
            self.client = None
    
    async def generate_code(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate code using the LLM based on the given prompt and context."""
        try:
            if not self.client:
                raise RuntimeError("OPENAI_API_KEY not set; LLM generation disabled")
            messages = [
                {
                    "role": "system",
                    "content": """You are a senior full-stack developer. Generate high-quality, production-ready code 
                    based on the user's requirements. Follow best practices, include proper error handling, 
                    and ensure the code is well-documented."""
                },
                {"role": "user", "content": prompt}
            ]
            
            if context:
                messages.insert(1, {
                    "role": "system",
                    "content": f"Additional context: {json.dumps(context, indent=2)}"
                })
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            raise
    
    async def generate_app_structure(self, requirements: Dict) -> Dict[str, str]:
        """Generate a complete app structure based on requirements."""
        try:
            prompt = f"""
            Based on the following requirements, generate a complete application structure.
            Return a JSON object where keys are file paths and values are the file contents.
            
            Requirements:
            {json.dumps(requirements, indent=2)}
            
            Include all necessary configuration files, source code, and documentation.
            """
            
            response = await self.generate_code(prompt)
            
            # Try to parse the response as JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If the response isn't valid JSON, try to extract JSON from code blocks
                import re
                json_match = re.search(r'```(?:json)?\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    raise ValueError("Failed to parse LLM response as JSON")
                    
        except Exception as e:
            logger.error(f"Error generating app structure: {e}")
            # Fallback to a default structure
            return self._get_default_structure(requirements)
    
    def _get_default_structure(self, requirements: Dict) -> Dict[str, str]:
        """Generate a default app structure if LLM generation fails."""
        return {
            "index.html": '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Generated App</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="icon" href="data:,">
    <style>body{min-height:100vh}</style>
    
    <!-- Bootstrap 5 (commonly required by tasks) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4">
    <div id="app" class="container">
        <h1 class="display-6 mb-3">Welcome to Your App</h1>
        <p>This is a default template. The app will be generated here.</p>
        <div id="total-sales" class="fw-bold"></div>
    </div>
    <script src="app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>''',
            "app.js": "// Your application JavaScript code will be generated here\nconsole.log('App initialized');",
            "README.md": "# Generated App\n\nThis is an automatically generated application.\n\n## Setup\n\n1. Clone this repository\n2. Open `index.html` in a web browser\n\n## Usage\n\nEdit the files to customize your application."
        }

# Create a singleton instance
llm_service = LLMService()
