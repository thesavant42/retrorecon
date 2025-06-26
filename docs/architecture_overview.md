# System Architecture Overview

This document summarizes the major runtime components of Retrorecon and illustrates how the database tables relate to each feature. The diagrams are written in [Mermaid](https://mermaid.js.org/) so they can be rendered directly in Markdown viewers that support it.

```mermaid
flowchart TB
    A((Browser UI)) --> B(Flask Server)
    subgraph B [Flask Application]
        C1[CDXFetcher]
        C2[JSONImporter]
        C3[ImportProgressTracker]
        C4[TagManager]
        C5[BulkActionAgent]
        C6[Notes API]
        C7[ScreenshotAgent]
        C8[SiteZipAgent]
        C9[SubdomainFetcher]
        C10[WebpackExploder]
        C11[DatabaseManager]
    end
    B --> D[(SQLite Database)]
    C1 -->|insert| urls
    C2 -->|insert| urls
    C3 -->|update| import_status
    C4 -->|update| urls
    C5 -->|update/delete| urls
    C6 -->|read/write| notes
    C7 -->|create| screenshots
    C8 -->|create| sitezips
    C9 -->|create| domains
    C10 -->|create| jobs
    C11 -->|load/save| D
```

The tables themselves are connected via the relationships shown below.

```mermaid
erDiagram
    urls {
        INTEGER id PK
        TEXT url
        TEXT domain
        TEXT timestamp
        INTEGER status_code
        TEXT mime_type
        TEXT tags
    }
    jobs {
        INTEGER id PK
        TEXT type
        TEXT domain
        TEXT status
        INTEGER progress
        TEXT result
        TIMESTAMP created_at
    }
    import_status {
        INTEGER id PK
        TEXT status
        TEXT detail
        INTEGER progress
        INTEGER total
    }
    notes {
        INTEGER id PK
        INTEGER url_id FK
        TEXT content
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    jwt_cookies {
        INTEGER id PK
        TEXT token
        TEXT header
        TEXT payload
        TEXT notes
        TIMESTAMP created_at
    }
    screenshots {
        INTEGER id PK
        TEXT url
        TEXT method
        TEXT screenshot_path
        TEXT thumbnail_path
        INTEGER status_code
        TEXT ip_addresses
        TIMESTAMP created_at
    }
    sitezips {
        INTEGER id PK
        TEXT url
        TEXT method
        TEXT zip_path
        TEXT screenshot_path
        TEXT thumbnail_path
        INTEGER status_code
        TEXT ip_addresses
        TIMESTAMP created_at
    }
    domains {
        INTEGER id PK
        TEXT root_domain
        TEXT subdomain
        TEXT source
        TEXT tags
        INTEGER cdx_indexed
        TIMESTAMP fetched_at
    }

    urls ||--o{ notes : has
    urls ||--|{ screenshots : captures
    urls ||--|{ sitezips : archives
    notes }o--|| urls : references
    domains ||--o{ urls : contains
```
