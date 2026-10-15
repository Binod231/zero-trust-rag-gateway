import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.cedar_auth import CedarAuthorizer
from app.opensearch_client import OpenSearchVectorClient
from app.bedrock_client import BedrockRAGClient

app = FastAPI(title="Zero-Trust Enterprise RAG Gateway", version="1.0.0")

cedar_authorizer = CedarAuthorizer()
vector_client = OpenSearchVectorClient()
bedrock_client = BedrockRAGClient()

class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000)
    user_id: str = Field(..., example="usr-4091")
    tenant_id: str = Field(..., example="acme-aerospace")
    department: str = Field(default="avionics-engineering")
    clearance_level: int = Field(default=2, ge=1, le=4)
    mfa_authenticated: bool = Field(default=True)
    network_source: str = Field(default="corp_network")

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "zero-trust-rag-gateway"}

@app.post("/v1/query")
async def execute_rag_query(request: QueryRequest):
    # 1. Zero-Trust Pre-Authorization with Cedar
    if not cedar_authorizer.is_query_authorized(
        request.user_id, request.tenant_id, request.clearance_level,
        request.department, request.mfa_authenticated, request.network_source
    ):
        raise HTTPException(status_code=403, detail="Forbidden: Rejected by enterprise Cedar policy.")

    # 2. Vector Embedding Generation
    query_vector = bedrock_client.generate_embeddings(request.prompt)

    # 3. Secure k-NN Vector Search with ABAC Metadata Filtering
    raw_documents = vector_client.search_similar_vectors(
        query_vector, request.tenant_id, request.department, request.clearance_level, top_k=4
    )

    # 4. Defense-in-Depth Verification
    verified = cedar_authorizer.filter_documents_batch(
        request.tenant_id, request.clearance_level, request.department, raw_documents
    )
    if not verified:
        return {"answer": "No authorized documents matching your clearance were found.", "documents_retrieved": 0}

    # 5. Server-Sent Events (SSE) Streaming Response
    context_texts = [d["content"] for d in verified]
    def event_stream():
        for token in bedrock_client.stream_converse_rag(request.prompt, context_texts):
            yield f"data: {token}

"
        yield "data: [DONE]

"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
