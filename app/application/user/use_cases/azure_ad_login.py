"""
Azure AD Login Use Case
Handles Azure AD authentication flow and user synchronization
"""
from typing import Optional, Dict, Any
from datetime import datetime

from ....domain.user.entities.user import User, UserRole, UserStatus
from ....domain.user.value_objects.email import Email
from ....domain.user.repository import UserRepository
from ....adapters.azure_ad_adapter import AzureADAdapter, AzureADUserInfo, AzureADTokenResponse
from ....services.token_service import TokenService
from ....core.logger import get_logger

logger = get_logger(__name__)


class AzureADLoginRequest:
    """Request model for Azure AD login"""
    
    def __init__(self, authorization_code: str, state: Optional[str] = None):
        self.authorization_code = authorization_code
        self.state = state


class AzureADLoginResponse:
    """Response model for Azure AD login"""
    
    def __init__(
        self,
        user: User,
        access_token: str,
        azure_ad_user: AzureADUserInfo,
        jwt_tokens: dict,
        is_new_user: bool = False
    ):
        self.user = user
        self.access_token = access_token
        self.azure_ad_user = azure_ad_user
        self.jwt_tokens = jwt_tokens
        self.is_new_user = is_new_user


class AzureADLoginUseCase:
    """
    Use case for Azure AD authentication
    Handles OAuth2 flow and user synchronization
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        azure_ad_adapter: AzureADAdapter,
        token_service: TokenService
    ):
        self.user_repository = user_repository
        self.azure_ad_adapter = azure_ad_adapter
        self.token_service = token_service
    
    async def execute(self, request: AzureADLoginRequest) -> AzureADLoginResponse:
        """
        Execute Azure AD login flow
        
        Args:
            request: Login request with authorization code
            
        Returns:
            Login response with user and token information
        """
        try:
            # Step 1: Exchange authorization code for access token
            logger.info("Exchanging authorization code for access token")
            token_response = await self.azure_ad_adapter.exchange_code_for_token(
                request.authorization_code
            )
            
            # Step 2: Get user information from Azure AD
            logger.info("Retrieving user information from Azure AD")
            azure_ad_user = await self.azure_ad_adapter.get_user_info(
                token_response.access_token
            )
            
            # Step 3: Check if user exists in our system
            logger.info(f"Checking if user exists: {azure_ad_user.mail}")
            try:
                logger.info("About to call find_by_email...")
                email_value_object = Email(azure_ad_user.mail)
                existing_user = await self.user_repository.find_by_email(email_value_object)
                logger.info(f"find_by_email completed. Existing user found: {existing_user is not None}")
                
                if existing_user:
                    logger.info(f"Existing user details: email={existing_user.email}, role={existing_user.role}, type={type(existing_user.role)}")
                    
                    # Fix role if it's a string instead of enum
                    if isinstance(existing_user.role, str):
                        logger.info(f"Converting role from string '{existing_user.role}' to enum")
                        try:
                            existing_user.role = UserRole(existing_user.role)
                            logger.info(f"Role converted successfully: {existing_user.role}")
                        except ValueError as e:
                            logger.warning(f"Invalid role '{existing_user.role}', defaulting to USER: {e}")
                            existing_user.role = UserRole.USER
                    
                    # Step 4a: Update existing user with latest Azure AD info
                    logger.info(f"About to update existing user: {existing_user.email}")
                    user = await self._update_existing_user(existing_user, azure_ad_user)
                    logger.info("User update completed")
                    is_new_user = False
                else:
                    # Step 4b: Create new user from Azure AD info
                    logger.info(f"About to create new user from Azure AD: {azure_ad_user.mail}")
                    user = await self._create_user_from_azure_ad(azure_ad_user)
                    logger.info("User creation completed")
                    is_new_user = True
            except Exception as e:
                logger.error(f"Error during user lookup/creation: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise
            
            # Step 5: Update last login
            user.update_last_login()
            await self.user_repository.save(user)
            
            # Step 6: Generate JWT tokens for our application
            logger.info("Generating JWT tokens for application")
            jwt_tokens = await self.token_service.generate_tokens(
                user_id=user.id,
                email=user.email,
                role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                permissions=user.permissions or [],
                remember_me=True,  # Azure AD users get refresh tokens
                additional_claims={
                    "azure_ad_id": azure_ad_user.id,
                    "auth_method": "azure_ad"
                }
            )
            
            logger.info(f"Azure AD login successful for user: {user.email}")
            
            return AzureADLoginResponse(
                user=user,
                access_token=token_response.access_token,
                azure_ad_user=azure_ad_user,
                jwt_tokens=jwt_tokens,
                is_new_user=is_new_user
            )
            
        except Exception as e:
            logger.error(f"Azure AD login failed: {e}")
            raise
    
    async def _update_existing_user(
        self, 
        existing_user: User, 
        azure_ad_user: AzureADUserInfo
    ) -> User:
        """
        Update existing user with latest Azure AD information
        
        Args:
            existing_user: Existing user in our system
            azure_ad_user: User information from Azure AD
            
        Returns:
            Updated user
        """
        logger.info(f"Updating existing user - role before: {existing_user.role}, type: {type(existing_user.role)}")
        
        # Update user information from Azure AD
        existing_user.full_name = azure_ad_user.display_name or existing_user.full_name
        existing_user.department = azure_ad_user.department or existing_user.department
        existing_user.phone = azure_ad_user.mobile_phone or existing_user.phone
        
        # Update metadata with Azure AD information
        existing_user.metadata.update({
            "azure_ad_id": azure_ad_user.id,
            "azure_ad_user_principal_name": azure_ad_user.user_principal_name,
            "azure_ad_job_title": azure_ad_user.job_title,
            "azure_ad_office_location": azure_ad_user.office_location,
            "azure_ad_business_phones": azure_ad_user.business_phones,
            "last_azure_ad_sync": datetime.utcnow().isoformat()
        })
        
        # Activate user if they were pending
        if existing_user.status == UserStatus.PENDING:
            existing_user.activate()
        
        existing_user.updated_at = datetime.utcnow()
        
        logger.info(f"Updated user - role after: {existing_user.role}, type: {type(existing_user.role)}")
        
        return existing_user
    
    async def _create_user_from_azure_ad(self, azure_ad_user: AzureADUserInfo) -> User:
        """
        Create new user from Azure AD information
        
        Args:
            azure_ad_user: User information from Azure AD
            
        Returns:
            Newly created user
        """
        # Determine user role based on Azure AD groups/roles
        role = self._determine_user_role(azure_ad_user)
        logger.info(f"Determined role: {role}, type: {type(role)}")
        
        # Create username from email
        username = azure_ad_user.mail.split('@')[0] if azure_ad_user.mail else azure_ad_user.id
        
        # Create user with Azure AD information
        user = User.create(
            email=azure_ad_user.mail,
            username=username,
            full_name=azure_ad_user.display_name or f"{azure_ad_user.given_name} {azure_ad_user.surname}",
            hashed_password="",  # No password for Azure AD users
            role=role
        )
        logger.info(f"Created user with role: {user.role}, type: {type(user.role)}")
        
        # Set additional information
        user.department = azure_ad_user.department
        user.phone = azure_ad_user.mobile_phone
        user.email_verified = True  # Azure AD users are pre-verified
        
        # Add Azure AD metadata
        user.metadata.update({
            "azure_ad_id": azure_ad_user.id,
            "azure_ad_user_principal_name": azure_ad_user.user_principal_name,
            "azure_ad_job_title": azure_ad_user.job_title,
            "azure_ad_office_location": azure_ad_user.office_location,
            "azure_ad_business_phones": azure_ad_user.business_phones,
            "created_via_azure_ad": True,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Activate user immediately
        user.activate()
        
        return user
    
    def _determine_user_role(self, azure_ad_user: AzureADUserInfo) -> UserRole:
        """
        Determine user role based on Azure AD groups and roles
        
        Args:
            azure_ad_user: User information from Azure AD
            
        Returns:
            Determined user role
        """
        # Check for admin groups/roles
        admin_indicators = [
            "admin", "administrator", "system admin", "global admin",
            "company admin", "tenant admin"
        ]
        
        # Check groups (if available)
        # Note: groups and roles are not currently available in AzureADUserInfo
        # This would require additional API calls to Microsoft Graph
        
        # Check job title
        if azure_ad_user.job_title:
            job_title = azure_ad_user.job_title.lower()
            if any(indicator in job_title for indicator in admin_indicators):
                return UserRole.ADMIN
        
        # Default to regular user
        return UserRole.USER


class SyncAzureADUsersUseCase:
    """
    Use case for syncing users from Azure AD
    Useful for bulk synchronization or admin operations
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        azure_ad_adapter: AzureADAdapter
    ):
        self.user_repository = user_repository
        self.azure_ad_adapter = azure_ad_adapter
    
    async def execute(self, query: str = "") -> Dict[str, Any]:
        """
        Sync users from Azure AD
        
        Args:
            query: Optional search query to filter users
            
        Returns:
            Sync results
        """
        try:
            # Get client credentials token for admin operations
            token_response = await self.azure_ad_adapter.get_client_credentials_token()
            
            # Search users in Azure AD
            azure_ad_users = await self.azure_ad_adapter.search_users(
                query, 
                token_response.access_token
            )
            
            synced_count = 0
            updated_count = 0
            created_count = 0
            
            for azure_ad_user in azure_ad_users:
                existing_user = await self.user_repository.find_by_email(azure_ad_user.mail)
                
                if existing_user:
                    # Update existing user
                    updated_user = await self._update_existing_user(existing_user, azure_ad_user)
                    await self.user_repository.save(updated_user)
                    updated_count += 1
                else:
                    # Create new user
                    new_user = await self._create_user_from_azure_ad(azure_ad_user)
                    await self.user_repository.save(new_user)
                    created_count += 1
                
                synced_count += 1
            
            logger.info(f"Azure AD sync completed: {synced_count} total, {created_count} created, {updated_count} updated")
            
            return {
                "total_synced": synced_count,
                "created": created_count,
                "updated": updated_count,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Azure AD sync failed: {e}")
            raise
    
    async def _update_existing_user(
        self, 
        existing_user: User, 
        azure_ad_user: AzureADUserInfo
    ) -> User:
        """Update existing user with Azure AD information"""
        # Similar to AzureADLoginUseCase._update_existing_user
        existing_user.full_name = azure_ad_user.display_name or existing_user.full_name
        existing_user.department = azure_ad_user.department or existing_user.department
        existing_user.phone = azure_ad_user.mobile_phone or existing_user.phone
        
        existing_user.metadata.update({
            "azure_ad_id": azure_ad_user.id,
            "azure_ad_user_principal_name": azure_ad_user.user_principal_name,
            "azure_ad_job_title": azure_ad_user.job_title,
            "azure_ad_office_location": azure_ad_user.office_location,
            "azure_ad_business_phones": azure_ad_user.business_phones,
            "last_azure_ad_sync": datetime.utcnow().isoformat()
        })
        
        existing_user.updated_at = datetime.utcnow()
        
        return existing_user
    
    async def _create_user_from_azure_ad(self, azure_ad_user: AzureADUserInfo) -> User:
        """Create new user from Azure AD information"""
        # Similar to AzureADLoginUseCase._create_user_from_azure_ad
        role = self._determine_user_role(azure_ad_user)
        username = azure_ad_user.mail.split('@')[0] if azure_ad_user.mail else azure_ad_user.id
        
        user = User.create(
            email=azure_ad_user.mail,
            username=username,
            full_name=azure_ad_user.display_name or f"{azure_ad_user.given_name} {azure_ad_user.surname}",
            hashed_password="",
            role=role
        )
        
        user.department = azure_ad_user.department
        user.phone = azure_ad_user.mobile_phone
        user.email_verified = True
        
        user.metadata.update({
            "azure_ad_id": azure_ad_user.id,
            "azure_ad_user_principal_name": azure_ad_user.user_principal_name,
            "azure_ad_job_title": azure_ad_user.job_title,
            "azure_ad_office_location": azure_ad_user.office_location,
            "azure_ad_business_phones": azure_ad_user.business_phones,
            # Note: groups and roles would require additional API calls
            "created_via_azure_ad": True,
            "created_at": datetime.utcnow().isoformat()
        })
        
        user.activate()
        
        return user
    
    def _determine_user_role(self, azure_ad_user: AzureADUserInfo) -> UserRole:
        """Determine user role based on Azure AD information"""
        # Similar to AzureADLoginUseCase._determine_user_role
        admin_indicators = [
            "admin", "administrator", "system admin", "global admin",
            "company admin", "tenant admin"
        ]
        
        # Note: groups and roles are not currently available in AzureADUserInfo
        # This would require additional API calls to Microsoft Graph
        
        if azure_ad_user.job_title:
            job_title = azure_ad_user.job_title.lower()
            if any(indicator in job_title for indicator in admin_indicators):
                return UserRole.ADMIN
        
        return UserRole.USER
