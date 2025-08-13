"""
Password Service - Handles password hashing and verification
"""
import passlib.context


class PasswordService:
    """
    Service for password operations
    Uses bcrypt for secure password hashing
    """
    
    def __init__(self, scheme: str = "bcrypt"):
        """
        Initialize password service
        
        Args:
            scheme: Hashing scheme to use (bcrypt, argon2, etc.)
        """
        self.pwd_context = passlib.context.CryptContext(schemes=[scheme], deprecated="auto")
    
    async def hash(self, plain_password: str) -> str:
        """
        Hash a plain password
        
        Args:
            plain_password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(plain_password)
    
    async def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a hashed password needs to be rehashed
        (e.g., if the hashing algorithm or parameters changed)
        
        Args:
            hashed_password: Current hashed password
            
        Returns:
            True if rehashing is needed
        """
        return self.pwd_context.needs_update(hashed_password)
    
    async def rehash_if_needed(
        self, 
        plain_password: str, 
        hashed_password: str
    ) -> tuple[bool, str]:
        """
        Rehash password if needed
        
        Args:
            plain_password: Plain text password
            hashed_password: Current hashed password
            
        Returns:
            Tuple of (needs_update, new_hash)
            If no update needed, returns (False, original_hash)
        """
        if self.needs_rehash(hashed_password):
            new_hash = await self.hash(plain_password)
            return True, new_hash
        return False, hashed_password