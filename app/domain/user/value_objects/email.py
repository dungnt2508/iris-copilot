"""
Email Value Object
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Email value object - immutable and self-validating
    """
    value: str
    
    def __post_init__(self):
        """Validate email on creation"""
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        # Convert to lowercase
        object.__setattr__(self, 'value', self.value.lower().strip())
        
        if not self._is_valid():
            raise ValueError(f"Invalid email format: {self.value}")
        
        if len(self.value) > 255:
            raise ValueError("Email cannot be longer than 255 characters")
    
    def _is_valid(self) -> bool:
        """Validate email format"""
        # RFC 5322 simplified regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, self.value) is not None
    
    @property
    def domain(self) -> str:
        """Get email domain"""
        return self.value.split('@')[1]
    
    @property
    def username(self) -> str:
        """Get email username part"""
        return self.value.split('@')[0]
    
    def is_corporate_email(self) -> bool:
        """Check if email is from a corporate domain (not free email provider)"""
        free_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'protonmail.com', 'icloud.com', 'mail.com', 'aol.com',
            'yandex.com', 'zoho.com'
        }
        return self.domain not in free_domains
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Email('{self.value}')"