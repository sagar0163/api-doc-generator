# Architecture Document: API Doc Generator

## 1. System Overview

API Documentation Generator analyzes source code to automatically extract API endpoint definitions and generate OpenAPI/Swagger specifications.

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Parser Module                               │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │ Flask/FastAPI│  │  Express    │                         │
│  │   Parser    │  │   Parser    │                         │
│  └─────────────┘  └─────────────┘                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenAPI Generator                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Output (JSON/YAML)                        │
└─────────────────────────────────────────────────────────────┘
```

## 3. File Structure

```
api-doc-generator/
├── specs/           # Documentation
└── README.md
```

---

*Document Version: 1.0*  
*Created: 2026-03-17*
