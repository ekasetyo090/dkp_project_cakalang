"""
Konfigurasi logging terpusat untuk aplikasi WhatsApp Bot
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

class LoggingConfig:
    """Konfigurasi logging terpusat"""
    
    # Base directory untuk log
    LOG_BASE_DIR = Path("logs")
    
    # Konfigurasi level logging per modul
    LOG_LEVELS = {
        'app': logging.INFO,
        'database': logging.DEBUG,
        'whatsapp': logging.INFO,
        'services': logging.INFO,
        'utils': logging.DEBUG
    }
    
    # Format log
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FORMAT_DETAILED = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO, detailed: bool = False):
        """
        Setup logger dengan konfigurasi terpusat
        
        Args:
            name: Nama logger (biasanya __name__)
            level: Level logging
            detailed: Jika True, gunakan format detail dengan file dan line number
            
        Returns:
            Logger object
        """
        # Extract module name dari full path
        module_name = name.split('.')[-1]
        
        # Tentukan kategori berdasarkan nama modul
        if 'database' in name.lower():
            category = 'database'
        elif 'whatsapp' in name.lower():
            category = 'whatsapp'
        elif 'services' in name.lower():
            category = 'services'
        elif 'utils' in name.lower():
            category = 'utils'
        else:
            category = 'app'
        
        # Buat directory jika belum ada
        log_dir = LoggingConfig.LOG_BASE_DIR / category
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Buat logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Cegah duplicate handlers
        if logger.handlers:
            return logger
        
        # Format log
        formatter = logging.Formatter(
            LoggingConfig.LOG_FORMAT_DETAILED if detailed else LoggingConfig.LOG_FORMAT
        )
        
        # File handler untuk semua level
        all_log_file = log_dir / f"{module_name}.log"
        file_handler = logging.FileHandler(all_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # File handler per level (opsional)
        for log_level in ['debug', 'info', 'warning', 'error']:
            level_dir = LoggingConfig.LOG_BASE_DIR / category / log_level
            level_dir.mkdir(parents=True, exist_ok=True)
            
            level_file = level_dir / f"{module_name}.log"
            level_handler = logging.FileHandler(level_file, encoding='utf-8')
            level_handler.setLevel(getattr(logging, log_level.upper()))
            
            # Filter hanya untuk level tertentu
            class LevelFilter(logging.Filter):
                def __init__(self, level):
                    super().__init__()
                    self.level = level
                
                def filter(self, record):
                    return record.levelno == getattr(logging, self.level.upper())
            
            level_handler.addFilter(LevelFilter(log_level))
            level_handler.setFormatter(formatter)
            logger.addHandler(level_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Rotating file handler untuk file utama
        rotating_handler = logging.handlers.RotatingFileHandler(
            all_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(rotating_handler)
        
        return logger
    
    @staticmethod
    def get_module_logger(module_name: str):
        """
        Mendapatkan logger yang sudah dikonfigurasi untuk modul tertentu
        
        Args:
            module_name: Nama modul (misalnya 'database.connection')
            
        Returns:
            Logger object
        """
        # Tentukan level berdasarkan kategori
        for category, level in LoggingConfig.LOG_LEVELS.items():
            if category in module_name.lower():
                return LoggingConfig.setup_logger(
                    module_name, 
                    level=level,
                    detailed=(level == logging.DEBUG)
                )
        
        # Default
        return LoggingConfig.setup_logger(
            module_name, 
            level=logging.INFO,
            detailed=False
        )

# Logger utama aplikasi
app_logger = LoggingConfig.get_module_logger('app.main')

def log_execution_time(func):
    """Decorator untuk mencatat waktu eksekusi fungsi"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger_name = f"{func.__module__}.{func.__name__}"
        logger = LoggingConfig.get_module_logger(logger_name)
        
        logger.info(f"Memulai eksekusi fungsi {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Fungsi {func.__name__} selesai dalam {execution_time:.2f} detik")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error dalam fungsi {func.__name__} setelah {execution_time:.2f} detik: {str(e)}", exc_info=True)
            raise
    
    return wrapper

def log_database_operation(func):
    """Decorator khusus untuk operasi database"""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger_name = f"{func.__module__}.{func.__name__}"
        logger = LoggingConfig.get_module_logger(logger_name)
        
        try:
            # Log query jika ada
            if 'query' in kwargs:
                logger.debug(f"Query: {kwargs['query']}")
            elif args and isinstance(args[0], str) and 'SELECT' in args[0]:
                logger.debug(f"Query: {args[0]}")
            
            result = func(*args, **kwargs)
            
            # Log hasil jika berupa data
            if result and hasattr(result, '__len__'):
                logger.debug(f"Query mengembalikan {len(result)} baris")
            
            return result
        except Exception as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise
    
    return wrapper