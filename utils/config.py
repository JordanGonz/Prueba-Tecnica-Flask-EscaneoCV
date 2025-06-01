import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Application configuration
CONFIG = {
    'APP_NAME': 'AI Recruitment System',
    'VERSION': '1.0.0',
    'DEBUG': True,
    
    # File upload settings
    'MAX_FILE_SIZE': 16 * 1024 * 1024,  # 16MB
    'ALLOWED_EXTENSIONS': {'pdf', 'docx', 'txt'},
    'UPLOAD_FOLDER': 'uploads',
    
    # Database settings
    'DATABASE_URL': os.environ.get('DATABASE_URL', 'sqlite:///recruitment.db'),
    
    # Security settings
    'SESSION_SECRET': os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production'),
    
    # Pagination settings
    'CANDIDATES_PER_PAGE': 20,
    'SEARCH_RESULTS_LIMIT': 50,
    
    # Logging settings
    'LOG_LEVEL': logging.DEBUG,
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

def get_config(key: str, default: Any = None) -> Any:
    """
    Get configuration value by key.
    
    Args:
        key (str): Configuration key
        default (Any): Default value if key not found
        
    Returns:
        Any: Configuration value
    """
    return CONFIG.get(key, default)

def validate_file_type(filename: str) -> bool:
    """
    Validate if file type is allowed for upload.
    
    Args:
        filename (str): Name of the file
        
    Returns:
        bool: True if file type is allowed
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = get_config('ALLOWED_EXTENSIONS', set())
    
    return extension in allowed_extensions

def get_upload_path() -> str:
    """
    Get the upload directory path.
    
    Returns:
        str: Upload directory path
    """
    upload_folder = get_config('UPLOAD_FOLDER', 'uploads')
    
    # Create upload directory if it doesn't exist
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
        logger.info(f"Created upload directory: {upload_folder}")
    
    return upload_folder

def get_database_url() -> str:
    """
    Get database URL from configuration.
    
    Returns:
        str: Database URL
    """
    return get_config('DATABASE_URL')

def is_development() -> bool:
    """
    Check if application is running in development mode.
    
    Returns:
        bool: True if in development mode
    """
    return get_config('DEBUG', False)

def get_app_info() -> Dict[str, str]:
    """
    Get application information.
    
    Returns:
        Dict[str, str]: Application info dictionary
    """
    return {
        'name': get_config('APP_NAME'),
        'version': get_config('VERSION'),
        'debug': str(get_config('DEBUG')),
        'database': get_database_url()
    }

def setup_logging():
    """
    Setup application logging configuration.
    """
    log_level = get_config('LOG_LEVEL', logging.INFO)
    log_format = get_config('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('recruitment_system.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    logger.info("Logging configuration setup completed")

# Initialize logging when module is imported
setup_logging()
