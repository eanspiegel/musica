# Frontend — Vue Architecture

> This document defines the structure, conventions, and mandatory patterns for the frontend.  
> Every decision here is final until explicitly revised via a documented ADR.

---

## Core Rule — The Frontend Has No Business Logic

The frontend is a **display and interaction layer only**. It MUST NOT:

- Validate business rules (e.g., "is this URL a valid YouTube link")
- Transform or process data beyond what is needed for display
- Make decisions about application state that belong to the backend
- Import or call any media/download library directly

**All logic lives in the backend. The frontend asks, the backend answers.**

---

## Stack

| Concern | Choice | Notes |
|---|---|---|
| Framework | **Vue 3** | Composition API only (no Options API) |
| Build tool | **Vite** | Fast dev server + HMR |
| Language | **TypeScript** | Strict mode enabled |
| State management | **Pinia** | One store per feature |
| Routing | **Vue Router 4** | Lazy-loaded routes |
| HTTP client | **Axios** | Behind an adapter (see below) |
| Component style | **`<script setup>`** | Always |
| CSS | **Tailwind CSS** | Utility-first |
| Testing | **Vitest + Vue Test Utils** | Unit + component tests |

---

## Directory Structure

```
frontend/
├── src/
│   ├── main.ts                  # App bootstrap
│   ├── App.vue                  # Root component
│   │
│   ├── adapters/                # Third-party integrations — never imported directly elsewhere
│   │   └── http.ts              # Wraps Axios — the ONLY file that knows Axios exists
│   │
│   ├── api/                     # Backend communication — one file per domain
│   │   ├── downloads.api.ts     # Calls /api/v1/downloads
│   │   ├── metadata.api.ts      # Calls /api/v1/metadata
│   │   ├── playlists.api.ts     # Calls /api/v1/playlists
│   │   └── search.api.ts        # Calls /api/v1/search
│   │
│   ├── stores/                  # Pinia stores — one per feature
│   │   ├── downloads.store.ts
│   │   ├── metadata.store.ts
│   │   └── playlists.store.ts
│   │
│   ├── router/
│   │   └── index.ts             # Route definitions with lazy imports
│   │
│   ├── views/                   # Page-level components (one per route)
│   │   ├── HomeView.vue
│   │   ├── DownloadView.vue
│   │   ├── PlaylistView.vue
│   │   └── TagsEditorView.vue
│   │
│   ├── components/              # Atomic Design
│   │   ├── atoms/               # Base building blocks (Button, Input, Badge…)
│   │   ├── molecules/           # Composed atoms (SearchBar, TrackCard…)
│   │   └── organisms/           # Feature sections (DownloadPanel, ResultsList…)
│   │
│   ├── composables/             # Reusable logic hooks (useDownload, useSearch…)
│   │
│   └── types/                   # TypeScript interfaces — mirrors backend response shapes
│       ├── track.types.ts
│       ├── playlist.types.ts
│       └── download.types.ts
│
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── .env.example
└── package.json
```

---

## Mandatory Patterns

### 1. HTTP Adapter (non-negotiable)

Axios is NEVER imported directly in stores, composables, or components.  
There is ONE adapter file: `src/adapters/http.ts`. Everything HTTP goes through it.

This means if Axios is replaced by `fetch`, `ky`, or any other client, only `http.ts` changes.

```typescript
// src/adapters/http.ts
import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

export const http = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    client.get<T>(url, config).then((r) => r.data),

  post: <T>(url: string, body?: unknown, config?: AxiosRequestConfig) =>
    client.post<T>(url, body, config).then((r) => r.data),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    client.delete<T>(url, config).then((r) => r.data),
}
```

**Usage in API files** (`src/api/downloads.api.ts`):
```typescript
import { http } from '@/adapters/http'
import type { DownloadJob, DownloadRequest } from '@/types/download.types'

export const downloadsApi = {
  create: (payload: DownloadRequest) =>
    http.post<DownloadJob>('/api/v1/downloads', payload),

  getAll: () =>
    http.get<DownloadJob[]>('/api/v1/downloads'),
}
```

### 2. Stores — No Direct API Calls in Components

Components NEVER call `api` functions directly. They talk to the store.  
Stores call `api` functions.

```
Component → Store action → API function → http adapter → Backend
```

```typescript
// src/stores/downloads.store.ts
import { defineStore } from 'pinia'
import { downloadsApi } from '@/api/downloads.api'
import type { DownloadJob } from '@/types/download.types'

export const useDownloadsStore = defineStore('downloads', () => {
  const jobs = ref<DownloadJob[]>([])
  const loading = ref(false)

  async function createDownload(url: string, format: string) {
    loading.value = true
    try {
      const job = await downloadsApi.create({ url, format })
      jobs.value.push(job)
    } finally {
      loading.value = false
    }
  }

  return { jobs, loading, createDownload }
})
```

### 3. Components — Presentation Only

Components receive data via props and emit events. They do NOT:
- Import stores directly in child/organism components (only views do)
- Contain conditional rendering based on business rules
- Transform backend data (that's the store's job)

```vue
<!-- Organism: receives data, emits events -->
<script setup lang="ts">
import type { DownloadJob } from '@/types/download.types'

defineProps<{ jobs: DownloadJob[] }>()
defineEmits<{ cancel: [id: string] }>()
</script>
```

### 4. Composables for Cross-Cutting Concerns

Reusable reactive logic goes into composables, not components or stores.

```typescript
// src/composables/useDownload.ts
export function useDownload() {
  const store = useDownloadsStore()

  const start = (url: string, format: string) => store.createDownload(url, format)

  return { jobs: store.jobs, loading: store.loading, start }
}
```

---

## Environment Variables

The `.env` file contains **exactly one variable**:

```dotenv
# .env.example
VITE_API_BASE_URL=http://localhost:8000
```

**Rules**:
- Only `VITE_` prefixed variables are exposed to the browser by Vite
- No secrets, tokens, or keys go in the frontend env — ever
- The `.env` file is NEVER committed. Only `.env.example` is versioned
- All business configuration (paths, limits, formats) lives in the backend

---

## Component Organization — Atomic Design

| Level | Location | Rule |
|---|---|---|
| Atom | `components/atoms/` | No props beyond primitives. No store access. |
| Molecule | `components/molecules/` | Composes atoms. No store access. |
| Organism | `components/organisms/` | Composes molecules. May receive complex props. |
| View | `views/` | Page entry. Only place that connects to stores. |

---

## TypeScript Conventions

- `strict: true` in `tsconfig.json` — no exceptions
- Types for backend response shapes live in `src/types/` and are named after the domain entity
- No `any`. Use `unknown` and narrow it when truly needed

---

## Routing

All routes are lazy-loaded:

```typescript
// src/router/index.ts
const routes = [
  {
    path: '/',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/download',
    component: () => import('@/views/DownloadView.vue'),
  },
]
```

---

## Scalability Considerations

- The `http` adapter abstraction makes HTTP client replacement zero-impact on business code
- Pinia stores are tree-shaken — unused stores add no bundle weight
- Atomic Design prevents component coupling — organisms can be restructured without touching atoms
- Lazy-loaded routes keep initial bundle size small regardless of how many views are added
- `src/types/` is the single source of truth for API shapes — if the backend schema changes, only types need updating
