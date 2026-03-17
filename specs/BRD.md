# Business Requirements Document (BRD): API Doc Generator

## 1. Project Overview

**Project Name:** API Documentation Generator  
**Type:** CLI Tool  
**Core Functionality:** Automatically scans codebase and generates API specification documentation (OpenAPI/Swagger) from Python (Flask, FastAPI) and Node.js (Express) projects.

**Target Users:** Developers who want automatic API documentation without manual annotation.

---

## 2. Features

- Auto-detect API endpoints
- Generate OpenAPI/Swagger specs
- Support Python (Flask, FastAPI) and Node.js (Express)
- Export to JSON/YAML

---

## 3. Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python |
| **Formats** | OpenAPI, Swagger, JSON, YAML |

---

## 4. User Stories

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US1 | As a developer, I want automatic API docs | Endpoints are detected and documented |

---

## 5. Requirements

- FR1: Parse Flask/FastAPI route decorators
- FR2: Parse Express routes
- FR3: Generate valid OpenAPI spec

---

*Document Version: 1.0*  
*Created: 2026-03-17*
