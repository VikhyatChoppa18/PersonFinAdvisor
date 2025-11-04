"""
Plaid service for bank account integration.
"""
from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from typing import Dict, Any, List
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class PlaidService:
    """Service for Plaid API integration."""
    
    def __init__(self):
        """Initialize Plaid client."""
        configuration = Configuration(
            host=getattr(plaid_api.environments, settings.PLAID_ENV),
            api_key={
                'clientId': settings.PLAID_CLIENT_ID,
                'secret': settings.PLAID_SECRET,
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    async def create_link_token(self, user_id: int) -> Dict[str, Any]:
        """Create a Plaid link token for user."""
        try:
            request = {
                'user': {
                    'client_user_id': str(user_id),
                },
                'client_name': 'Personal Finance AI',
                'products': ['transactions'],
                'country_codes': ['US'],
                'language': 'en',
            }
            
            response = self.client.link_token_create(request)
            return {
                'link_token': response['link_token'],
                'expiration': response['expiration'],
            }
        except Exception as e:
            logger.error("Error creating link token", error=str(e))
            raise
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token."""
        try:
            request = {'public_token': public_token}
            response = self.client.item_public_token_exchange(request)
            return {
                'access_token': response['access_token'],
                'item_id': response['item_id'],
            }
        except Exception as e:
            logger.error("Error exchanging public token", error=str(e))
            raise
    
    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get accounts from Plaid."""
        try:
            request = {'access_token': access_token}
            response = self.client.accounts_get(request)
            return response['accounts']
        except Exception as e:
            logger.error("Error getting accounts", error=str(e))
            raise
    
    async def get_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get transactions from Plaid."""
        try:
            request = {
                'access_token': access_token,
                'start_date': start_date,
                'end_date': end_date,
            }
            response = self.client.transactions_get(request)
            return response['transactions']
        except Exception as e:
            logger.error("Error getting transactions", error=str(e))
            raise

