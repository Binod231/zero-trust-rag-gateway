resource "aws_verifiedpermissions_policy_store" "rag_store" {
  validation_settings {
    mode = "STRICT"
  }
  description = "Zero-Trust Enterprise RAG Authorization Store"
}

resource "aws_verifiedpermissions_schema" "rag_schema" {
  policy_store_id = aws_verifiedpermissions_policy_store.rag_store.id
  definition {
    value = file("${path.module}/../policies/schema.json")
  }
}

resource "aws_verifiedpermissions_policy" "tenant_isolation_policy" {
  policy_store_id = aws_verifiedpermissions_policy_store.rag_store.id
  definition {
    static {
      description = "Strict multi-tenant boundary and ABAC clearance enforcement"
      statement   = file("${path.module}/../policies/rag_gateway_policy.cedar")
    }
  }
  depends_on = [aws_verifiedpermissions_schema.rag_schema]
}

output "policy_store_id" {
  value = aws_verifiedpermissions_policy_store.rag_store.id
}
