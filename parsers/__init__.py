"""
Parsers module for extracting text from various CV file formats.
Supports PDF, DOCX, and plain text files.
"""

from .pdf_parser import extract_text_from_pdf
from .docx_parser import extract_text_from_docx
from .text_cleaner import clean_and_extract_info

__all__ = ['extract_text_from_pdf', 'extract_text_from_docx', 'clean_and_extract_info']
