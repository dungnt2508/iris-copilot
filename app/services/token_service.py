"""
Token Service - Handles JWT token generation and verification
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
import secrets


class TokenService:
    """
    Service for JWT token operations
    Handles access tokens and refresh tokens
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        """
        Initialize token service
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm (HS256, RS256, etc.)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    async def generate_tokens(
        self,
        user_id: str,
        email: str,
        role: str,
        permissions: List[str],
        remember_me: bool = False,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate access and refresh tokens
        
        Args:
            user_id: User ID
            email: User email
            role: User role
            permissions: User permissions
            remember_me: Whether to generate refresh token
            additional_claims: Additional JWT claims
            
        Returns:
            Dictionary with tokens and expiration info
        """
        # Access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token_data = {
            "sub": user_id,
            "email": email,
            "role": role,
            "permissions": permissions,
            "type": "access",
            "exp": datetime.utcnow() + access_token_expires,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        if additional_claims:
            access_token_data.update(additional_claims)
        
        access_token = jwt.encode(
            access_token_data, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        result = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": access_token_data["exp"],
            "expires_in": self.access_token_expire_minutes * 60  # in seconds
        }
        
        # Refresh token (if remember_me is True)
        if remember_me:
            refresh_token_expires = timedelta(days=self.refresh_token_expire_days)
            refresh_token_data = {
                "sub": user_id,
                "email": email,
                "type": "refresh",
                "exp": datetime.utcnow() + refresh_token_expires,
                "iat": datetime.utcnow(),
                "jti": secrets.token_urlsafe(16)
            }
            
            refresh_token = jwt.encode(
                refresh_token_data,
                self.secret_key,
                algorithm=self.algorithm
            )
            
            result["refresh_token"] = refresh_token
            result["refresh_expires_at"] = refresh_token_data["exp"]
        
        return result
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode an access token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "permissions": payload.get("permissions", []),
                "jti": payload.get("jti"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            }
            
        except JWTError:
            return None
        except Exception:
            return None
    
    async def verify_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a refresh token
        
        Args:
            refresh_token: Refresh JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check token type
            if payload.get("type") != "refresh":
                return None
            
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "jti": payload.get("jti"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            }
            
        except JWTError:
            return None
        except Exception:
            return None
    
    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token without verification (for debugging only)
        
        Args:
            token: JWT token
            
        Returns:
            Decoded payload without verification
        """
        try:
            return jwt.get_unverified_claims(token)
        except Exception:
            return None
    
    async def revoke_token(self, jti: str) -> None:
        """
        Revoke a token by its JTI (JWT ID)
        This would typically add the JTI to a blacklist in Redis/DB
        
        Args:
            jti: JWT ID to revoke
        """
        # Implementation would depend on your revocation strategy
        # Could use Redis, database, or in-memory cache
        pass
    
    async def is_token_revoked(self, jti: str) -> bool:
        """
        Check if a token is revoked
        
        Args:
            jti: JWT ID to check
            
        Returns:
            True if token is revoked
        """
        # Implementation would check against revocation list
        return False