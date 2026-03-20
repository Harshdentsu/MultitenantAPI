# 🧠 Multi-Tenant AI Assistant API

A scalable **multi-tenant AI assistant backend** built using **Django REST Framework + LangChain + OpenAI**, designed to support multiple organizations with **isolated knowledge bases and assistants**.

---

# 🚀 Overview

This project solves a key problem:

> Multiple organizations need their own AI assistants with private knowledge — without building separate systems.

### ✅ Solution:

* Single backend system
* Multi-tenant architecture
* Organization-specific assistants
* Document-based knowledge (RAG)

Each organization:

* Registers users
* Uploads documents
* Gets an AI assistant trained on their own data

---

# 🏗️ Architecture

The system is divided into 3 main apps:

---

## 1️⃣ Core App (Authentication & Multi-Tenancy)

Handles:

* User authentication
* Organization mapping

### 🔹 Key Concept:

Each user is linked to an **organization**

### 🔹 Flow:

1. User sends credentials
2. API validates user
3. Token is generated
4. Token is used for all further requests

---

## 2️⃣ Documents App (Knowledge Ingestion)

Handles:

* Document uploads
* Text processing
* Chunk storage

### 🔹 Flow:

1. User sends request with token
2. Uploads document
3. Document is:

   * Parsed
   * Split into chunks using `RecursiveCharacterTextSplitter`
4. Chunks are stored in DB **linked to organization**

---

## 3️⃣ Knowledge App (Q&A Engine)

Handles:

* Question answering
* Embeddings
* Retrieval (RAG)
* Conversation history

### 🔹 Flow:

1. User sends question
2. System:

   * Generates embedding using OpenAI
   * Searches relevant chunks (same organization only)
3. Retrieved context → passed to LLM
4. Response generated
5. Conversation stored using sessions

---

# 🧠 Core Concepts Used

* **Multi-Tenancy** (organization-level isolation)
* **RAG (Retrieval-Augmented Generation)**
* **Embeddings (OpenAI)**
* **Chunking (RecursiveCharacterTextSplitter)**
* **Semantic Search**
* **Session-based Conversation Memory**
* **JWT AUTHENTICATION**

---

# 🔐 Authentication Flow

### Endpoint:

```
POST /api/token/
```

### Body:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

### Response:

```json
{
  "access": "your_token_here"
}
```

👉 Use this token in headers:

```
Authorization: Bearer <token>
```

---

# 📂 API Endpoints

---

## 📌 1. Generate Token

```
POST /api/token/
```

---

## 📌 2. Upload Document

```
POST /api/documents/upload/
```

### Headers:

```
Authorization: Bearer <token>
```

### Description:

* Uploads document
* Processes and stores chunks under user's organization

---

## 📌 3. Get Documents

```
GET /api/documents/
```

### Headers:

```
Authorization: Bearer <token>
```

### Description:

* Fetch all documents for the logged-in user's organization

---

## 📌 4. Ask Question

```
POST /api/knowledge/ask/
```

### Headers:

```
Authorization: Bearer <token>
```

### Body:

```json
{
  "question": "Your question here"
}
```

### Description:

* Performs semantic search on organization documents
* Generates AI response using OpenAI
* Maintains conversation history

---

# 🔥 Key Features

* ✅ Multi-tenant architecture
* ✅ Organization-level data isolation
* ✅ Document-based AI assistant
* ✅ Semantic search using embeddings
* ✅ Conversation history support
* ✅ Token-based authentication
* ✅ Scalable backend design
---

# ⚙️ Tech Stack

* Django REST Framework
* LangChain
* OpenAI (Embeddings + LLM)
* PostgreSQL / DB for storage

---
# 🧪 Example Use Case

1. Organization A uploads documents
2. Organization B uploads different documents

👉 When:

* User A asks → only Org A data is used
* User B asks → only Org B data is used

✔ Complete isolation
✔ Single backend

---

For any queries or collaboration, reach out!
