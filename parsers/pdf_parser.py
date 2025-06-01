import logging
import PyPDF2
from io import BytesIO

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """
    Extract text content from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
        
    Raises:
        Exception: If PDF processing fails
    """
    try:
        extracted_text = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                logger.warning(f"PDF {file_path} is encrypted, attempting to decrypt")
                try:
                    pdf_reader.decrypt("")  # Try empty password first
                except:
                    raise Exception("PDF is password protected and cannot be processed")
            
            # Extract text from all pages
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                    logger.debug(f"Extracted text from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                    continue
        
        if not extracted_text.strip():
            raise Exception("No text could be extracted from the PDF")
            
        logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF: {file_path}")
        return extracted_text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        raise Exception(f"Failed to process PDF file: {str(e)}")

def extract_text_from_pdf_bytes(pdf_bytes):
    """
    Extract text content from PDF bytes.
    
    Args:
        pdf_bytes (bytes): PDF file content as bytes
        
    Returns:
        str: Extracted text content
        
    Raises:
        Exception: If PDF processing fails
    """
    try:
        extracted_text = ""
        
        pdf_stream = BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        
        # Check if PDF is encrypted
        if pdf_reader.is_encrypted:
            logger.warning("PDF is encrypted, attempting to decrypt")
            try:
                pdf_reader.decrypt("")  # Try empty password first
            except:
                raise Exception("PDF is password protected and cannot be processed")
        
        # Extract text from all pages
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
                logger.debug(f"Extracted text from page {page_num + 1}")
            except Exception as e:
                logger.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                continue
        
        if not extracted_text.strip():
            raise Exception("No text could be extracted from the PDF")
            
        logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF bytes")
        return extracted_text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF bytes: {str(e)}")
        raise Exception(f"Failed to process PDF file: {str(e)}")
