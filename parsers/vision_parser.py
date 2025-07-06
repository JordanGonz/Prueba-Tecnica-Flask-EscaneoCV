import os
import json
import base64
import logging
from io import BytesIO
from typing import Dict, List, Optional, Any, Union
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
from openai import OpenAI 
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POPPLER_PATH = os.path.join(BASE_DIR, "..", "poppler", "Library", "bin")
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found. Vision parsing will be disabled.")
    openai_client = None
else:
    openai_client = OpenAI(
        api_key=OPENAI_API_KEY,
        organization=OPENAI_ORG_ID
    )

def pdf_to_images(pdf_path: str) -> List[Image.Image]:
    """
    Convert PDF to list of PIL Images.
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        List[Image.Image]: List of PIL images
    """
    try:
        images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=3, poppler_path=POPPLER_PATH) # Max 3 pages
        logger.info(f"Converted PDF to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        return []

def pdf_bytes_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """
    Convert PDF bytes to list of PIL Images.
    
    Args:
        pdf_bytes (bytes): PDF file as bytes
        
    Returns:
        List[Image.Image]: List of PIL images
    """
    try:
        images = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=3, poppler_path=POPPLER_PATH) # Max 3 pages
        logger.info(f"Converted PDF bytes to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF bytes to images: {str(e)}")
        return []

def image_to_base64(image: Image.Image, format: str = "JPEG", max_size: tuple = (1024, 1024)) -> str:
    """
    Convert PIL Image to base64 string.
    
    Args:
        image (Image.Image): PIL Image
        format (str): Image format (JPEG, PNG)
        max_size (tuple): Maximum size for resizing
        
    Returns:
        str: Base64 encoded image
    """
    try:
        # Resize image if too large
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB' and format == 'JPEG':
            image = image.convert('RGB')
        
        buffer = BytesIO()
        image.save(buffer, format=format, quality=85, optimize=True)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return ""

def analyze_cv_with_vision(images: List[Image.Image]) -> Dict:
    """
    Analyze CV images using OpenAI Vision API.
    
    Args:
        images (List[Image.Image]): List of CV page images
        
    Returns:
        Dict: Extracted candidate information
    """
    if not openai_client:
        logger.warning("OpenAI client not available. Skipping vision analysis.")
        return {}
    
    try:
        # Convert images to base64
        image_messages = []
        for i, image in enumerate(images[:4]):  # Analyze max 2 pages
            base64_image = image_to_base64(image)
            if base64_image:
                image_messages.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        
        if not image_messages:
            logger.warning("No valid images to analyze")
            return {}
        
        # Prepare the prompt for CV analysis
        prompt = """
        Extract the following information from this CV/resume image and return it in valid JSON format:

        {
        "name": "Full name of the candidate",
        "email": "Email address",
        "phone": "Phone number",
        "skills": ["list", "of", "technical", "skills"],
        "experience": [
            {
            "title": "Job title",
            "company": "Company name",
            "duration": "Duration or dates",
            "description": "Brief description of role"
            }
        ],
        "education": [
            {
            "degree": "Degree name or academic level (e.g. Bachelor, Master, Egresado, Estudiante)",
            "institution": "Name of the University, College or School",
            "year": "Year of graduation or range if available",
            "field": "Field of study (e.g. Ingeniería en Sistemas, Informática, etc.)",
            "status": "Graduado, Egresado, Estudiante, o vacío si no se menciona"
            }
        ],
        "languages": ["list", "of", "languages"],
        "certifications": ["list", "of", "certifications"],
        "summary": "Brief professional summary"
        }

        Important considerations:
        - The candidate might mention education informally (e.g. 'estoy estudiando en...', 'egresado de...') in sections like 'Sobre mí'.
        - The education section may include both university and high school information. Try to include both when available.
        - Look for clues like 'Título obtenido:', 'Universidad:', 'Egresado:', 'Estudiante:', 'Licenciatura en...', 'Ingeniero en...', etc.
        - If multiple degrees are mentioned (e.g., colegio and universidad), list both as separate entries.
        - Do your best to extract all available details, even if incomplete.
        - JSON must be valid and structured as described.
        """

        
        # Create message with text and images
        content = [{"type": "text", "text": prompt}] + image_messages
        messages = [{"role": "user", "content": content}]
        
        # Call OpenAI Vision API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Latest OpenAI model with vision capabilities
            messages=messages,  # type: ignore
            max_tokens=2000,
           response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            logger.info("Successfully analyzed CV with OpenAI Vision")
        else:
            result = {}
            logger.warning("Empty response from OpenAI Vision")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing CV with vision: {str(e)}")
        return {}

def extract_cv_data_with_vision(file_path: str, file_type: str) -> Dict:
    """
    Extract CV data using vision analysis.
    
    Args:
        file_path (str): Path to CV file
        file_type (str): Type of file (pdf, docx, jpg, png)
        
    Returns:
        Dict: Extracted candidate information
    """
    try:
        images = []
        
        if file_type.lower() == 'pdf':
            images = pdf_to_images(file_path)
        elif file_type.lower() in ['jpg', 'jpeg', 'png']:
            # If it's already an image
            image = Image.open(file_path)
            images = [image]
        elif file_type.lower() == 'docx':
            from docx2pdf import convert
            import tempfile
            import pythoncom
            
            pythoncom.CoInitialize() 
            with tempfile.TemporaryDirectory() as tmpdirname:
                temp_pdf = os.path.join(tmpdirname, "converted.pdf")
                convert(file_path, temp_pdf)
                images = pdf_to_images(temp_pdf)
                
            pythoncom.CoUninitialize()
        
        if not images:
            logger.warning(f"No images generated from {file_type} file")
            return {}
        
        # Analyze with OpenAI Vision
        result = analyze_cv_with_vision(images)
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting CV data with vision: {str(e)}")
        return {}

def generate_text_embedding(text: str, model_name: str = "text-embedding-3-small") -> List[float]:
    """
    Generate embedding for a given text using OpenAI Embedding API.
    
    Args:
        text (str): Input text to embed (up to 8000 tokens).
        model_name (str): Name of the embedding model to use.
        
    Returns:
        List[float]: Embedding vector (1536 dimensions for text-embedding-3-small)
    """
    if not openai_client:
        logger.warning("OpenAI client not available. Skipping embedding generation.")
        return [0.0] * 1536
    
    try:
        cleaned_text = text.strip().replace("\n", " ")[:8000]
        if not cleaned_text:
            return [0.0] * 1536

        response = openai_client.embeddings.create(
            model=model_name,
            input=[cleaned_text]
        )
        
        embedding = response.data[0].embedding
        logger.info(f"Generated embedding ({len(embedding)} dims) for text: {cleaned_text[:60]}...")
        return embedding

    except Exception as e:
        logger.error(f"OpenAI embedding error: {str(e)}")
        return [0.0] * 1536


def search_candidates_semantic(query: str, candidate_embeddings: List[Dict], top_k: int = 10, similarity_threshold: float = 0.6) -> List[Dict]:
    """
    Perform semantic search using embeddings and filter by similarity threshold.

    Args:
        query (str): Search query
        candidate_embeddings (List[Dict]): List of candidates with embeddings
        top_k (int): Max results to return
        similarity_threshold (float): Minimum similarity to consider a match

    Returns:
        List[Dict]: Top matching candidates with similarity >= threshold
    """
    if not openai_client:
        logger.warning("OpenAI client not available. Skipping semantic search.")
        return []

    try:
        query_embedding = generate_text_embedding(query)
        if not query_embedding:
            return []

        results = []
        for candidate in candidate_embeddings:
            emb = candidate.get('embedding', [])
            if not emb:
                continue

            sim = cosine_similarity(query_embedding, emb)
            if sim >= similarity_threshold:  # ← AQUI EL FILTRO
                results.append({
                    'candidate': candidate,
                    'similarity': sim
                })

        results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = []
        for r in results[:top_k]:
            candidate = r['candidate'].copy()
            candidate['similarity'] = round(r['similarity'], 4)
            top_results.append(candidate)

        return top_results

    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        return []


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1 (List[float]): First vector
        vec2 (List[float]): Second vector
        
    Returns:
        float: Cosine similarity score
    """
    try:
        import numpy as np
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {str(e)}")
        return 0.0
    
def analyze_text_with_openai(text: str) -> Dict:
    """
    Analiza texto plano de CV (.docx o .txt) con GPT-4o y devuelve un JSON estructurado robusto.
    """
    if not openai_client:
        logger.warning("OpenAI client not available.")
        return {}

    try:
        prompt = f"""
Eres un experto en análisis de hojas de vida. A partir del siguiente texto extrae la información estructurada en formato JSON.
Detecta las secciones aunque estén nombradas diferente o con estilos desordenados (como EDUCACIÓN, Formación Académica, Estudios, etc).
Si un dato no está presente, usa una cadena vacía o una lista vacía. Mantén el formato, no expliques nada, solo devuelve el JSON.

Ejemplo de salida:
{{
  "name": "Nombre completo",
  "email": "Correo electrónico",
  "phone": "Número de teléfono",
  "skills": ["Habilidad1", "Habilidad2"],
  "experience": [
    {{
      "title": "Cargo o Rol",
      "company": "Nombre de la empresa",
      "duration": "Año o periodo"
    }}
  ],
  "education": [
    {{
      "degree": "Nombre del título o grado",
      "institution": "Nombre de la institución",
      "year": "Año si está disponible"
    }}
  ],
  "languages": ["Idioma1", "Idioma2"],
  "certifications": ["Certificación1", "Certificación2"],
  "summary": "Resumen profesional o perfil si existe"
}}

Texto del CV:
{text[:12000]}  <!-- GPT-4o permite hasta 128k tokens, usamos 12k para evitar cortes. -->
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )

        result = response.choices[0].message.content.strip()

        # Validación robusta del JSON devuelto
        try:
            data = json.loads(result)
            return data
        except json.JSONDecodeError as json_err:
            logger.error(f"Respuesta malformada del modelo: {result}")
            return {}

    except Exception as e:
        logger.error(f"Error al analizar texto plano: {str(e)}")
        return {}
