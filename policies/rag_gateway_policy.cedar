// Policy 1: Zero-Trust Multi-Tenant Isolation (Default Forbid across tenants)
forbid (
    principal,
    action,
    resource
)
when {
    principal.tenantId != resource.tenantId
};

// Policy 2: Permit Query on Tenant Space if MFA is satisfied
permit (
    principal,
    action == Enterprise::Action::"Query",
    resource
)
when {
    principal.tenantId == resource.tenantId &&
    context.mfaAuthenticated == true
};

// Policy 3: Clearance Hierarchy for Document Retrieval
permit (
    principal,
    action == Enterprise::Action::"Retrieve",
    resource
)
when {
    principal.tenantId == resource.tenantId &&
    principal.clearanceLevel >= resource.classificationLevel &&
    (
        resource.department == "general" ||
        resource.department == principal.department ||
        principal.role in ["Executive", "ComplianceAuditor"]
    )
};

// Policy 4: Hard restriction on Level 4 (Restricted) documents from non-corporate networks
forbid (
    principal,
    action,
    resource
)
when {
    resource.classificationLevel == 4 &&
    context.networkSource != "corp_network"
};
