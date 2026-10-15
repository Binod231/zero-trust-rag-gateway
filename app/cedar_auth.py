import boto3
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class CedarAuthorizer:
    def __init__(self):
        self.client = boto3.client("verifiedpermissions", region_name=settings.AWS_REGION)
        self.policy_store_id = settings.POLICY_STORE_ID

    def is_query_authorized(
        self,
        user_id: str,
        tenant_id: str,
        clearance_level: int,
        department: str,
        mfa_authenticated: bool,
        network_source: str
    ) -> bool:
        try:
            response = self.client.is_authorized(
                policyStoreId=self.policy_store_id,
                principal={"entityType": "Enterprise::User", "entityId": user_id},
                action={"actionType": "Enterprise::Action", "actionId": "Query"},
                resource={"entityType": "Enterprise::TenantSpace", "entityId": tenant_id},
                context={
                    "contextMap": {
                        "mfaAuthenticated": {"boolean": mfa_authenticated},
                        "networkSource": {"string": network_source}
                    }
                },
                entities={
                    "entityList": [
                        {
                            "identifier": {"entityType": "Enterprise::User", "entityId": user_id},
                            "attributes": {
                                "tenantId": {"string": tenant_id},
                                "department": {"string": department},
                                "clearanceLevel": {"long": clearance_level},
                                "role": {"string": "Employee"}
                            }
                        },
                        {
                            "identifier": {"entityType": "Enterprise::TenantSpace", "entityId": tenant_id},
                            "attributes": {"tenantId": {"string": tenant_id}}
                        }
                    ]
                }
            )
            return response.get("decision") == "ALLOW"
        except Exception as e:
            logger.error("Failed to evaluate Cedar policy: %s", str(e))
            return False

    def filter_documents_batch(
        self,
        tenant_id: str,
        clearance_level: int,
        department: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        authorized_docs = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            if (
                metadata.get("tenant_id") == tenant_id
                and clearance_level >= metadata.get("classification_level", 4)
                and metadata.get("department", "general") in ["general", department]
            ):
                authorized_docs.append(doc)
            else:
                logger.warning("Rejected doc %s at defense-in-depth gate", doc.get("id"))
        return authorized_docs
