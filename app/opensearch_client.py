import boto3
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from app.config import settings

class OpenSearchVectorClient:
    def __init__(self):
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, settings.AWS_REGION, "aoss") if credentials else None
        host = settings.OPENSEARCH_ENDPOINT.replace("https://", "")

        if auth:
            self.client = OpenSearch(
                hosts=[{"host": host, "port": 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=15
            )
        else:
            self.client = None
        self.index_name = settings.OPENSEARCH_INDEX

    def search_similar_vectors(
        self,
        query_vector: List[float],
        tenant_id: str,
        department: str,
        clearance_level: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        query_dsl = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding_vector": {
                                    "vector": query_vector,
                                    "k": top_k
                                }
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"metadata.tenant_id": tenant_id}},
                        {"range": {"metadata.classification_level": {"lte": clearance_level}}},
                        {
                            "bool": {
                                "should": [
                                    {"term": {"metadata.department": department}},
                                    {"term": {"metadata.department": "general"}}
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    ]
                }
            }
        }
        res = self.client.search(body=query_dsl, index=self.index_name)
        hits = res.get("hits", {}).get("hits", [])
        return [
            {
                "id": h["_id"],
                "content": h["_source"]["content"],
                "metadata": h["_source"]["metadata"]
            }
            for h in hits
        ]
