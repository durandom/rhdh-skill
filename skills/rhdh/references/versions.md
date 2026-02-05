# RHDH Version Compatibility Matrix

This reference provides the complete version compatibility information for RHDH dynamic plugins.

## Version Summary

| RHDH Version | Backstage Version | create-app Version | Status |
|--------------|-------------------|-------------------|--------|
| next         | 1.42.5           | 0.7.3             | Pre-release |
| 1.8          | 1.42.5           | 0.7.3             | Current |
| 1.7          | 1.39.1           | 0.6.2             | Supported |
| 1.6          | 1.36.1           | 0.5.25            | Supported |
| 1.5          | 1.35.1           | 0.5.24            | Legacy |

## RHDH 1.8 / next (Pre-release)

Based on [Backstage 1.42.5](https://backstage.io/docs/releases/v1.42.0)

Bootstrap command:
```bash
npx @backstage/create-app@0.7.3
```

### Frontend Packages

| Package | Version |
|---------|---------|
| `@backstage/catalog-model` | `1.7.5` |
| `@backstage/config` | `1.3.3` |
| `@backstage/core-app-api` | `1.18.0` |
| `@backstage/core-components` | `0.17.5` |
| `@backstage/core-plugin-api` | `1.10.9` |
| `@backstage/integration-react` | `1.2.9` |

### Backend Packages

| Package | Version |
|---------|---------|
| `@backstage/backend-app-api` | `1.2.6` |
| `@backstage/backend-defaults` | `0.12.0` |
| `@backstage/backend-dynamic-feature-service` | `0.7.3` |
| `@backstage/backend-plugin-api` | `1.4.2` |
| `@backstage/catalog-model` | `1.7.5` |
| `@backstage/cli-node` | `0.2.14` |
| `@backstage/config` | `1.3.3` |
| `@backstage/config-loader` | `1.10.2` |

## RHDH 1.7

Based on [Backstage 1.39.1](https://backstage.io/docs/releases/v1.39.0)

Bootstrap command:
```bash
npx @backstage/create-app@0.6.2
```

### Frontend Packages

| Package | Version |
|---------|---------|
| `@backstage/catalog-model` | `1.7.4` |
| `@backstage/config` | `1.3.2` |
| `@backstage/core-app-api` | `1.17.0` |
| `@backstage/core-components` | `0.17.2` |
| `@backstage/core-plugin-api` | `1.10.7` |
| `@backstage/integration-react` | `1.2.7` |

### Backend Packages

| Package | Version |
|---------|---------|
| `@backstage/backend-app-api` | `1.2.3` |
| `@backstage/backend-defaults` | `0.10.0` |
| `@backstage/backend-dynamic-feature-service` | `0.7.0` |
| `@backstage/backend-plugin-api` | `1.3.1` |
| `@backstage/catalog-model` | `1.7.4` |
| `@backstage/cli-node` | `0.2.13` |
| `@backstage/config` | `1.3.2` |
| `@backstage/config-loader` | `1.10.1` |

## RHDH 1.6

Based on [Backstage 1.36.1](https://backstage.io/docs/releases/v1.36.0)

Bootstrap command:
```bash
npx @backstage/create-app@0.5.25
```

### Frontend Packages

| Package | Version |
|---------|---------|
| `@backstage/catalog-model` | `1.7.3` |
| `@backstage/config` | `1.3.2` |
| `@backstage/core-app-api` | `1.15.5` |
| `@backstage/core-components` | `0.16.4` |
| `@backstage/core-plugin-api` | `1.10.4` |
| `@backstage/integration-react` | `1.2.4` |

### Backend Packages

| Package | Version |
|---------|---------|
| `@backstage/backend-app-api` | `1.2.0` |
| `@backstage/backend-defaults` | `0.8.1` |
| `@backstage/backend-dynamic-feature-service` | `0.6.0` |
| `@backstage/backend-plugin-api` | `1.2.0` |
| `@backstage/catalog-model` | `1.7.3` |
| `@backstage/cli-node` | `0.2.13` |
| `@backstage/config` | `1.3.2` |
| `@backstage/config-loader` | `1.9.6` |

## RHDH 1.5

Based on [Backstage 1.35.1](https://backstage.io/docs/releases/v1.35.0)

Bootstrap command:
```bash
npx @backstage/create-app@0.5.24
```

### Frontend Packages

| Package | Version |
|---------|---------|
| `@backstage/catalog-model` | `1.7.3` |
| `@backstage/config` | `1.3.2` |
| `@backstage/core-app-api` | `1.15.4` |
| `@backstage/core-components` | `0.16.3` |
| `@backstage/core-plugin-api` | `1.10.3` |
| `@backstage/integration-react` | `1.2.3` |

### Backend Packages

| Package | Version |
|---------|---------|
| `@backstage/backend-app-api` | `1.1.1` |
| `@backstage/backend-defaults` | `0.7.0` |
| `@backstage/backend-dynamic-feature-service` | `0.5.3` |
| `@backstage/backend-plugin-api` | `1.1.1` |
| `@backstage/catalog-model` | `1.7.3` |
| `@backstage/cli-node` | `0.2.12` |
| `@backstage/config` | `1.3.2` |
| `@backstage/config-loader` | `1.9.5` |

## Checking Package Versions

To check versions for packages not listed above:

### Frontend packages
Check the [`package.json`](https://github.com/redhat-developer/rhdh/blob/main/packages/app/package.json) in the `app` package.

### Backend packages
Check the [`package.json`](https://github.com/redhat-developer/rhdh/blob/main/packages/backend/package.json) in the `backend` package.

For specific RHDH versions, switch to the appropriate branch (e.g., `release-1.7`).

## CLI Version Compatibility

The `@red-hat-developer-hub/cli` version should match the target RHDH version:

```bash
# Always use the latest compatible version
npx @red-hat-developer-hub/cli@latest plugin export
```

Check the [Version Matrix](https://github.com/redhat-developer/rhdh/blob/main/docs/dynamic-plugins/versions.md) for specific CLI versions if needed.
