"""
Password Value Object
"""
import re
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Password:
    """
    Password value object - immutable and self-validating
    """
    value: str
    
    # Password requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def __post_init__(self):
        """Validate password on creation"""
        if not self.value:
            raise ValueError("Password cannot be empty")
        
        errors = self._validate()
        if errors:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")
    
    def _validate(self) -> List[str]:
        """
        Validate password against security requirements
        Returns list of validation errors
        """
        errors = []
        
        # Check length
        if len(self.value) < self.MIN_LENGTH:
            errors.append(f"Must be at least {self.MIN_LENGTH} characters long")
        
        if len(self.value) > self.MAX_LENGTH:
            errors.append(f"Cannot be longer than {self.MAX_LENGTH} characters")
        
        # Check character requirements
        if self.REQUIRE_UPPERCASE and not any(c.isupper() for c in self.value):
            errors.append("Must contain at least one uppercase letter")
        
        if self.REQUIRE_LOWERCASE and not any(c.islower() for c in self.value):
            errors.append("Must contain at least one lowercase letter")
        
        if self.REQUIRE_DIGIT and not any(c.isdigit() for c in self.value):
            errors.append("Must contain at least one digit")
        
        if self.REQUIRE_SPECIAL and not any(c in self.SPECIAL_CHARS for c in self.value):
            errors.append(f"Must contain at least one special character ({self.SPECIAL_CHARS})")
        
        # Check for common weak patterns
        if self._has_weak_patterns():
            errors.append("Password contains weak patterns")
        
        return errors
    
    def _has_weak_patterns(self) -> bool:
        """Check for common weak password patterns"""
        weak_patterns = [
            r'(.)\1{2,}',  # Same character repeated 3+ times
            r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        ]
        
        lower_value = self.value.lower()
        for pattern in weak_patterns:
            if re.search(pattern, lower_value):
                return True
        
        # Check for common weak passwords
        common_weak = [
            'password', 'qwerty', 'admin', 'letmein', 'welcome',
            'monkey', 'dragon', 'master', 'superman'
        ]
        
        for weak in common_weak:
            if weak in lower_value:
                return True
        
        return False
    
    def calculate_strength(self) -> str:
        """
        Calculate password strength
        Returns: 'weak', 'medium', 'strong', or 'very_strong'
        """
        score = 0
        
        # Length scoring
        if len(self.value) >= 8:
            score += 1
        if len(self.value) >= 12:
            score += 1
        if len(self.value) >= 16:
            score += 1
        
        # Character diversity scoring
        if any(c.isupper() for c in self.value):
            score += 1
        if any(c.islower() for c in self.value):
            score += 1
        if any(c.isdigit() for c in self.value):
            score += 1
        if any(c in self.SPECIAL_CHARS for c in self.value):
            score += 1
        
        # Entropy bonus
        unique_chars = len(set(self.value))
        if unique_chars >= len(self.value) * 0.7:
            score += 1
        
        # Map score to strength
        if score <= 3:
            return "weak"
        elif score <= 5:
            return "medium"
        elif score <= 7:
            return "strong"
        else:
            return "very_strong"
    
    def __str__(self) -> str:
        # Never expose the actual password value
        return "***PROTECTED***"
    
    def __repr__(self) -> str:
        return f"Password(strength={self.calculate_strength()})"