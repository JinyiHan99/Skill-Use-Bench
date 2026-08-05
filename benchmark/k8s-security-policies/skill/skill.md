---
name: k8s-security-policies
description: 'Use this skill when creating or reviewing Kubernetes manifests. Ensures all pods, deployments, and namespaces follow security best practices including non-root execution, capability dropping, read-only filesystems, network policies, and RBAC.'
---

# Kubernetes Security Policies

## Overview

Every Kubernetes manifest produced must comply with security hardening requirements. These policies apply at the pod level, namespace level, and cluster level. Manifests that violate these policies are considered insecure and must be remediated before deployment.

This skill enforces the Pod Security Standards at the "restricted" profile level, which is the most secure configuration recommended by Kubernetes for production workloads.

## When to Use

- When creating any Kubernetes YAML manifest (Deployment, StatefulSet, DaemonSet, Job, CronJob, Pod)
- When reviewing existing manifests for security compliance
- When setting up new namespaces
- When defining RBAC roles and bindings
- When configuring network access between services

## Pod Security Context Requirements

### Rule S1: runAsNonRoot Must Be True

Every pod spec must explicitly set `runAsNonRoot: true` in the security context. Running containers as root is the single most common Kubernetes security vulnerability.

```yaml
# REQUIRED in every pod spec
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
```

Do not omit `runAsNonRoot` even if you set a specific `runAsUser` — both must be present. The `runAsNonRoot` flag acts as a safety net that prevents container startup if the image defaults to root.

### Rule S2: Drop ALL Capabilities

Every container must explicitly drop all Linux capabilities and only add back the specific ones needed (if any). Most applications require zero capabilities.

```yaml
# REQUIRED in every container spec
containers:
  - name: app
    securityContext:
      capabilities:
        drop:
          - ALL
        # Only add back if absolutely required:
        # add:
        #   - NET_BIND_SERVICE  # only if binding to ports < 1024
```

Never use `add: ["ALL"]` or `add: ["SYS_ADMIN"]`. If a container genuinely needs capabilities beyond the default dropped set, document why in a comment above the `add` section.

### Rule S3: Read-Only Root Filesystem

Every container must set `readOnlyRootFilesystem: true`. Applications that need writable directories must use explicit `emptyDir` volume mounts for those specific paths.

```yaml
containers:
  - name: app
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
      - name: tmp
        mountPath: /tmp
      - name: cache
        mountPath: /app/cache
volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir:
      sizeLimit: 100Mi
```

Never set `readOnlyRootFilesystem: false`. If the application writes to the filesystem, identify the specific writable paths and mount `emptyDir` volumes for them.

### Rule S4: Seccomp Profile Must Be Set

Every pod must specify a seccomp profile. Use `RuntimeDefault` as the baseline — it blocks dangerous system calls while allowing normal application operation.

```yaml
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault
```

Do not use `Unconfined` as the seccomp type. If a workload requires system calls not allowed by `RuntimeDefault`, create a custom seccomp profile rather than disabling seccomp entirely.

### Rule S5: Privilege Escalation Disabled

Every container must set `allowPrivilegeEscalation: false` to prevent child processes from gaining more privileges than the parent.

```yaml
containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      privileged: false
```

Never set `privileged: true`. Never omit `allowPrivilegeEscalation` — it defaults to `true` if not explicitly set.

## Namespace Security

### Rule S6: Pod Security Labels on Namespace

Every namespace must have pod security admission labels that enforce the restricted profile:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

All three labels (`enforce`, `audit`, `warn`) must be present and set to `restricted`. Do not use `baseline` or `privileged` profiles in production namespaces.

## Network Policies

### Rule S7: NetworkPolicy Must Exist

Every namespace must have at least one NetworkPolicy resource. Start with a default-deny policy, then add specific allow rules:

```yaml
# Default deny all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress

---
# Allow specific traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-ingress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: my-service
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-gateway
      ports:
        - port: 8080
          protocol: TCP
```

Never deploy services without a corresponding NetworkPolicy. Default-deny must always be the first policy in a namespace.

## RBAC

### Rule S8: RBAC Roles Must Be Defined

Every service account used by a workload must have an explicit Role (or ClusterRole) and RoleBinding. Never use the `default` service account for production workloads.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: production
  automountServiceAccountToken: false  # mount only when needed

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-binding
  namespace: production
subjects:
  - kind: ServiceAccount
    name: my-app-sa
    namespace: production
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```

RBAC rules must follow least privilege:
- Use `Role` (namespaced) over `ClusterRole` whenever possible
- Specify exact resource names where feasible (not wildcards)
- Never grant `*` verbs or `*` resources
- Set `automountServiceAccountToken: false` on the ServiceAccount unless the pod needs API access

## Resource Limits

### Rule S9: Resource Requests and Limits Required

Every container must specify both `requests` and `limits` for CPU and memory:

```yaml
containers:
  - name: app
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "500m"
```

Never deploy a container without resource limits — unbounded containers can starve other workloads on the node.

## Verification Checklist

Before marking a manifest complete:

- [ ] `runAsNonRoot: true` in pod securityContext
- [ ] `runAsUser` set to non-zero value (typically 1000)
- [ ] `capabilities.drop: ["ALL"]` in every container
- [ ] `readOnlyRootFilesystem: true` in every container
- [ ] `seccompProfile.type: RuntimeDefault` in pod securityContext
- [ ] `allowPrivilegeEscalation: false` in every container
- [ ] `privileged: false` in every container (or omitted, which defaults to false)
- [ ] Namespace has `pod-security.kubernetes.io/enforce: restricted` label
- [ ] At least one NetworkPolicy exists (default-deny first)
- [ ] ServiceAccount created with `automountServiceAccountToken: false`
- [ ] Role/ClusterRole + RoleBinding defined with least privilege
- [ ] Resource `requests` and `limits` set for CPU and memory
