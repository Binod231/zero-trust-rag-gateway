import json
import boto3
import logging
from typing import List, Generator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)

class BedrockRAGClient:
    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    def generate_embeddings(self, text: str) -> List[float]:
        payload = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
        response = self.client.invoke_model(
            modelId=settings.BEDROCK_EMBEDDING_MODEL,
            contentType="application/json",
            accept="application/json",
            body=payload
        )
        return json.loads(response["body"].read())["embedding"]

    def stream_converse_rag(self, user_prompt: str, context_chunks: List[str]) -> Generator[str, None, None]:
        formatted_context = "

---

".join(
            [f"[Document Reference {i+1}]: {chunk}" for i, chunk in enumerate(context_chunks)]
        )
        system_message = (
            "You are an enterprise AI assistant operating within a strict Zero-Trust enclave. "
            "Answer the query solely using the verified references below. "
            "If unavailable, state that the information cannot be found."
        )
        messages = [{
            "role": "user",
            "content": [{"text": f"Context References:
{formatted_context}

Query: {user_prompt}"}]
        }]

        try:
            yield from self._invoke_converse_stream(settings.BEDROCK_PRIMARY_MODEL, system_message, messages)
        except ClientError as e:
            logger.warning("Primary model failed: %s. Falling back to %s", str(e), settings.BEDROCK_FALLBACK_MODEL)
            yield from self._invoke_converse_stream(settings.BEDROCK_FALLBACK_MODEL, system_message, messages)

    def _invoke_converse_stream(self, model_id: str, system: str, messages: list):
        response = self.client.converse_stream(
            modelId=model_id,
            messages=messages,
            system=[{"text": system}],
            inferenceConfig={"temperature": 0.1, "maxTokens": 2048, "topP": 0.9}
        )
        for event in response.get("stream", []):
            if "contentBlockDelta" in event:
                text = event["contentBlockDelta"].get("delta", {}).get("text")
                if text:
                    yield text
