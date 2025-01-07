"""Security configuration"""

from typing import Optional, List
from dataclasses import dataclass
from os import getenv
from pathlib import Path

@dataclass
class SecurityConfig:
    """Конфігурація безпеки"""
    secret_key: str
    jwt_algorithm: str
    jwt_expiration: int  # в хвилинах
    allowed_ips: List[str]
    rate_limit: int  # запитів за хвилину
    max_request_size: int  # в мегабайтах
    ssl_cert_path: Optional[Path]
    ssl_key_path: Optional[Path]
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Створення конфігурації з змінних оточення"""
        # Отримання та валідація списку дозволених IP
        allowed_ips_str = getenv('ALLOWED_IPS', '127.0.0.1')
        allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',')]
        
        # Отримання шляхів до SSL сертифікатів
        ssl_cert = getenv('SSL_CERT_PATH')
        ssl_key = getenv('SSL_KEY_PATH')
        
        return cls(
            secret_key=getenv('SECRET_KEY', 'your-secret-key'),
            jwt_algorithm=getenv('JWT_ALGORITHM', 'HS256'),
            jwt_expiration=int(getenv('JWT_EXPIRATION_MINUTES', '60')),
            allowed_ips=allowed_ips,
            rate_limit=int(getenv('RATE_LIMIT', '100')),
            max_request_size=int(getenv('MAX_REQUEST_SIZE_MB', '10')),
            ssl_cert_path=Path(ssl_cert) if ssl_cert else None,
            ssl_key_path=Path(ssl_key) if ssl_key else None
        )
    
    @property
    def has_ssl(self) -> bool:
        """Перевірка наявності SSL сертифікатів"""
        return bool(
            self.ssl_cert_path and
            self.ssl_key_path and
            self.ssl_cert_path.exists() and
            self.ssl_key_path.exists()
        )
    
    def validate_ip(self, ip: str) -> bool:
        """Перевірка IP адреси"""
        return ip in self.allowed_ips or ip == '127.0.0.1'
    
    @property
    def cors_settings(self) -> dict:
        """Налаштування CORS"""
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    
    @property
    def security_headers(self) -> dict:
        """Налаштування заголовків безпеки"""
        return {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline';"
            )
        }
    
    def get_jwt_settings(self) -> dict:
        """Налаштування JWT"""
        return {
            "secret_key": self.secret_key,
            "algorithm": self.jwt_algorithm,
            "access_token_expire_minutes": self.jwt_expiration
        }
    
    def get_rate_limit_settings(self) -> dict:
        """Налаштування обмеження запитів"""
        return {
            "times": self.rate_limit,
            "seconds": 60
        } 