"""
API Key Authentication System
Provides secure API key authentication with rate limiting, scopes, and usage tracking
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import logging
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from models import APIKeyScope, APIKeyStatus, APIKeyCreate, APIKeyResponse, APIKeyUsage
from database import get_admin_client
import json
import time
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages API key generation, validation, and usage tracking"""
    
    def __init__(self):
        self.rate_limiter = defaultdict(list)  # Simple in-memory rate limiter
        self.cache = {}  # Cache for validated API keys
        self.cache_ttl = 300  # 5 minutes cache
        
    def generate_api_key(self, client_id: str, prefix: str = "sk") -> str:
        """Generate a secure API key with proper format"""
        # Generate cryptographically secure random key
        key_bytes = secrets.token_bytes(32)
        key_string = secrets.token_urlsafe(32)
        
        # Create formatted key: prefix_clientprefix_randomstring
        client_prefix = str(client_id)[:8].replace('-', '')
        api_key = f"{prefix}_{client_prefix}_{key_string}"
        
        return api_key
    
    def hash_api_key(self, api_key: str) -> str:
        """Create a secure hash of the API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(self, client_id: uuid.UUID, key_data: APIKeyCreate) -> tuple[str, APIKeyResponse]:
        """Create a new API key for a client"""
        try:
            db_client = get_admin_client()
            if not db_client:
                raise Exception("Database not configured")
            
            # Generate API key
            api_key = self.generate_api_key(str(client_id))
            key_hash = self.hash_api_key(api_key)
            
            # Store in database
            key_record = {
                "client_id": str(client_id),
                "key_hash": key_hash,
                "name": key_data.name,
                "scopes": [scope.value for scope in key_data.scopes],
                "status": APIKeyStatus.ACTIVE.value,
                "rate_limit": key_data.rate_limit,
                "requests_made": 0,
                "expires_at": key_data.expires_at.isoformat() if key_data.expires_at else None,
                "description": key_data.description,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = db_client.table("client_api_keys").insert(key_record).execute()
            
            if not response.data:
                raise Exception("Failed to create API key")
            
            key_info = response.data[0]
            
            # Return API key (only shown once) and key info
            api_key_response = APIKeyResponse(
                key_id=uuid.UUID(key_info["key_id"]),
                client_id=uuid.UUID(key_info["client_id"]),
                name=key_info["name"],
                key_preview=api_key[:8] + "..." + api_key[-4:],
                scopes=[APIKeyScope(scope) for scope in key_info["scopes"]],
                status=APIKeyStatus(key_info["status"]),
                rate_limit=key_info["rate_limit"],
                requests_made=key_info["requests_made"],
                last_used=None,
                expires_at=datetime.fromisoformat(key_info["expires_at"]) if key_info["expires_at"] else None,
                created_at=datetime.fromisoformat(key_info["created_at"]),
                description=key_info["description"]
            )
            
            logger.info(f"✅ Created API key '{key_data.name}' for client {client_id}")
            return api_key, api_key_response
            
        except Exception as e:
            logger.error(f"❌ Failed to create API key: {e}")
            raise Exception(f"Failed to create API key: {str(e)}")
    
    async def validate_api_key(self, api_key: str, required_scope: Optional[APIKeyScope] = None) -> Dict[str, Any]:
        """Validate API key and check permissions"""
        try:
            # Check cache first
            cache_key = f"api_key:{hashlib.md5(api_key.encode()).hexdigest()}"
            cached_result = self.cache.get(cache_key)
            
            if cached_result and time.time() - cached_result['cached_at'] < self.cache_ttl:
                key_info = cached_result['data']
            else:
                # Validate from database
                key_hash = self.hash_api_key(api_key)
                db_client = get_admin_client()
                
                response = db_client.table("client_api_keys").select("*").eq("key_hash", key_hash).execute()
                
                if not response.data:
                    raise HTTPException(status_code=401, detail="Invalid API key")
                
                key_info = response.data[0]
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': key_info,
                    'cached_at': time.time()
                }
            
            # Check if key is active
            if key_info["status"] != APIKeyStatus.ACTIVE.value:
                raise HTTPException(status_code=401, detail="API key is not active")
            
            # Check expiration
            if key_info["expires_at"]:
                expires_at = datetime.fromisoformat(key_info["expires_at"])
                if datetime.utcnow() > expires_at:
                    raise HTTPException(status_code=401, detail="API key has expired")
            
            # Check rate limiting
            await self._check_rate_limit(key_info["key_id"], key_info["rate_limit"])
            
            # Check scope permissions
            key_scopes = [APIKeyScope(scope) for scope in key_info["scopes"]]
            
            if required_scope and required_scope not in key_scopes and APIKeyScope.FULL_ACCESS not in key_scopes:
                raise HTTPException(status_code=403, detail=f"API key does not have required scope: {required_scope.value}")
            
            # Update last used timestamp
            await self._update_key_usage(key_info["key_id"])
            
            return {
                "key_id": key_info["key_id"],
                "client_id": key_info["client_id"],
                "scopes": key_scopes,
                "rate_limit": key_info["rate_limit"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ API key validation failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    async def _check_rate_limit(self, key_id: str, rate_limit: int):
        """Check if API key has exceeded rate limit"""
        current_time = time.time()
        hour_ago = current_time - 3600  # 1 hour ago
        
        # Clean old requests
        self.rate_limiter[key_id] = [req_time for req_time in self.rate_limiter[key_id] if req_time > hour_ago]
        
        # Check rate limit
        if len(self.rate_limiter[key_id]) >= rate_limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Add current request
        self.rate_limiter[key_id].append(current_time)
    
    async def _update_key_usage(self, key_id: str):
        """Update API key usage statistics"""
        try:
            db_client = get_admin_client()
            
            # Update requests count and last used timestamp
            db_client.table("client_api_keys").update({
                "requests_made": "requests_made + 1",  # Use SQL increment
                "last_used": datetime.utcnow().isoformat()
            }).eq("key_id", key_id).execute()
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to update key usage: {e}")
    
    async def list_api_keys(self, client_id: uuid.UUID) -> List[APIKeyResponse]:
        """List all API keys for a client"""
        try:
            db_client = get_admin_client()
            
            response = db_client.table("client_api_keys").select("*").eq("client_id", str(client_id)).order("created_at", desc=True).execute()
            
            keys = []
            for key_data in response.data:
                key_response = APIKeyResponse(
                    key_id=uuid.UUID(key_data["key_id"]),
                    client_id=uuid.UUID(key_data["client_id"]),
                    name=key_data["name"],
                    key_preview="sk_" + "*" * 8 + key_data["key_hash"][-4:],  # Safe preview
                    scopes=[APIKeyScope(scope) for scope in key_data["scopes"]],
                    status=APIKeyStatus(key_data["status"]),
                    rate_limit=key_data["rate_limit"],
                    requests_made=key_data["requests_made"],
                    last_used=datetime.fromisoformat(key_data["last_used"]) if key_data["last_used"] else None,
                    expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data["expires_at"] else None,
                    created_at=datetime.fromisoformat(key_data["created_at"]),
                    description=key_data["description"]
                )
                keys.append(key_response)
            
            return keys
            
        except Exception as e:
            logger.error(f"❌ Failed to list API keys: {e}")
            raise Exception(f"Failed to list API keys: {str(e)}")
    
    async def revoke_api_key(self, key_id: uuid.UUID, client_id: uuid.UUID) -> bool:
        """Revoke an API key"""
        try:
            db_client = get_admin_client()
            
            response = db_client.table("client_api_keys").update({
                "status": APIKeyStatus.REVOKED.value,
                "revoked_at": datetime.utcnow().isoformat()
            }).eq("key_id", str(key_id)).eq("client_id", str(client_id)).execute()
            
            # Clear from cache
            for cache_key in list(self.cache.keys()):
                if self.cache[cache_key]['data'].get('key_id') == str(key_id):
                    del self.cache[cache_key]
                    break
            
            logger.info(f"✅ Revoked API key {key_id} for client {client_id}")
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"❌ Failed to revoke API key: {e}")
            raise Exception(f"Failed to revoke API key: {str(e)}")

# Global API key manager instance
api_key_manager = APIKeyManager()

# FastAPI dependencies for API key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)
jwt_bearer = HTTPBearer(auto_error=False)

async def get_api_key_from_header(api_key: str = Depends(api_key_header)) -> Optional[str]:
    """Extract API key from header"""
    return api_key

async def get_api_key_from_query(api_key: str = Depends(api_key_query)) -> Optional[str]:
    """Extract API key from query parameter"""
    return api_key

async def authenticate_request(
    request: Request,
    api_key_header: Optional[str] = Depends(get_api_key_from_header),
    api_key_query: Optional[str] = Depends(get_api_key_from_query),
    jwt_token: Optional[HTTPAuthorizationCredentials] = Depends(jwt_bearer),
    required_scope: Optional[APIKeyScope] = None
) -> Dict[str, Any]:
    """
    Unified authentication that supports both API keys and JWT tokens
    """
    
    # Try API key authentication first
    api_key = api_key_header or api_key_query
    if api_key:
        try:
            auth_result = await api_key_manager.validate_api_key(api_key, required_scope)
            auth_result["auth_type"] = "api_key"
            logger.debug(f"✅ API key authentication successful for client {auth_result['client_id']}")
            return auth_result
        except HTTPException as e:
            logger.warning(f"⚠️ API key authentication failed: {e.detail}")
            # Fall through to JWT authentication
    
    # Try JWT authentication
    if jwt_token:
        try:
            from app import verify_token  # Import JWT verification function
            token_data = verify_token(jwt_token.credentials)
            auth_result = {
                "client_id": str(token_data.client_id),
                "email": token_data.email,
                "auth_type": "jwt",
                "scopes": [APIKeyScope.FULL_ACCESS]  # JWT tokens have full access
            }
            logger.debug(f"✅ JWT authentication successful for client {token_data.client_id}")
            return auth_result
        except Exception as e:
            logger.warning(f"⚠️ JWT authentication failed: {e}")
    
    # No valid authentication found
    raise HTTPException(
        status_code=401, 
        detail="Authentication required. Provide a valid API key (X-API-Key header or api_key query param) or JWT token (Authorization header)."
    )

# Scope-specific dependencies
async def require_read_access(auth_data: Dict[str, Any] = Depends(lambda: authenticate_request(None, required_scope=APIKeyScope.READ))) -> Dict[str, Any]:
    """Require read access"""
    return auth_data

async def require_write_access(auth_data: Dict[str, Any] = Depends(lambda: authenticate_request(None, required_scope=APIKeyScope.WRITE))) -> Dict[str, Any]:
    """Require write access"""
    return auth_data

async def require_admin_access(auth_data: Dict[str, Any] = Depends(lambda: authenticate_request(None, required_scope=APIKeyScope.ADMIN))) -> Dict[str, Any]:
    """Require admin access"""
    return auth_data

async def require_analytics_access(auth_data: Dict[str, Any] = Depends(lambda: authenticate_request(None, required_scope=APIKeyScope.ANALYTICS))) -> Dict[str, Any]:
    """Require analytics access"""
    return auth_data 