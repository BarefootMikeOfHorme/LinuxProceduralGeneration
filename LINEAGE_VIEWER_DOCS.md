# LineageViewer React Component - Documentation

## Overview

The **LineageViewer** is a comprehensive React component for visualizing VaultMind Forge lineage records, asset scores, and rejection reasons. It provides an intuitive interface for exploring generation history, filtering records, and analyzing quality metrics.

## Features

✅ **Multi-View Display**
- Grid View - Card-based layout for quick overview
- List View - Tabular display with sortable columns
- Timeline View - Chronological visualization

✅ **Advanced Filtering**
- Filter by Job ID
- Filter by Branch
- Filter by Status (completed, failed, running)
- Search by Run ID or Job ID

✅ **Comprehensive Visualization**
- Asset scores and validation results
- Rejection reasons with improvement suggestions
- Failed metrics highlighting
- System information display
- Execution metrics and timing

✅ **Interactive Features**
- Detailed modal view for each record
- Real-time statistics dashboard
- Responsive design
- Hover effects and animations

---

## Installation

### Option 1: Standalone HTML (CDN)

Use the provided demo HTML file that loads React from CDN:

```bash
# Open in browser
examples/lineage-viewer-demo.html
```

### Option 2: React Project Integration

1. **Install Dependencies:**
```bash
npm install react react-dom
```

2. **Copy Component Files:**
```
src/frontend/components/
├── LineageViewer.jsx
└── LineageViewer.css
```

3. **Import in Your App:**
```javascript
import LineageViewer from './components/LineageViewer';
import './components/LineageViewer.css';

function App() {
  return <LineageViewer apiBaseUrl="http://localhost:3000/api" />;
}
```

---

## API Endpoint

The component requires a backend API endpoint that returns lineage records.

### GET /api/lineage

**Query Parameters:**
- `jobId` (optional) - Filter by job ID
- `branch` (optional) - Filter by branch name
- `status` (optional) - Filter by execution status

**Response Format:**
```json
{
  "success": true,
  "data": {
    "records": [
      {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2025-10-30T12:00:00.000Z",
        "lineage": {
          "lineage_id": "...",
          "job_id": "job-123",
          "branch": "main",
          "parent": null
        },
        "job": {
          "id": "job-123",
          "output_type": "character",
          "style_tags": ["anime", "cel-shaded"]
        },
        "assets": [
          {
            "asset_path": "output/img.png",
            "asset_name": "img.png",
            "checksum": "sha256...",
            "validated": true,
            "metrics": { "score": 0.85 }
          }
        ],
        "validations": [
          {
            "file": "output/img.png",
            "score": 0.85,
            "status": "PASS",
            "passed": true
          }
        ],
        "rejections": [
          {
            "asset_path": "output/failed.png",
            "reason": "Score below threshold",
            "validation_score": 0.45,
            "failed_metrics": ["sharpness", "anatomy"],
            "suggestions": [
              "Increase resolution or adjust denoising steps",
              "Use reference images or anatomy ControlNet"
            ]
          }
        ],
        "execution": {
          "start_time": "2025-10-30T12:00:00.000Z",
          "end_time": "2025-10-30T12:05:00.000Z",
          "duration_ms": 300000,
          "status": "completed"
        },
        "system": {
          "platform": "win32",
          "arch": "x64",
          "node_version": "v18.0.0",
          "memory_used_mb": 125.4
        }
      }
    ],
    "count": 1
  }
}
```

---

## Component Props

### LineageViewer

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiBaseUrl` | string | `'http://localhost:3000/api'` | Base URL for API requests |

**Example:**
```jsx
<LineageViewer apiBaseUrl="https://api.example.com/v1" />
```

---

## Usage Examples

### Basic Usage

```jsx
import LineageViewer from './components/LineageViewer';

function App() {
  return (
    <div className="app">
      <LineageViewer />
    </div>
  );
}
```

### Custom API URL

```jsx
<LineageViewer apiBaseUrl="https://production-api.example.com/api" />
```

### With Environment Variable

```jsx
<LineageViewer apiBaseUrl={process.env.REACT_APP_API_URL} />
```

---

## Component Structure

### Main Component: LineageViewer

The parent component that manages state and orchestrates child components.

**State:**
- `lineageRecords` - Array of fetched lineage records
- `loading` - Loading state boolean
- `error` - Error message string
- `selectedRecord` - Currently selected record for detail view
- `filters` - Filter criteria object
- `viewMode` - Current view mode ('grid' | 'list' | 'timeline')

**Key Functions:**
- `fetchLineageRecords()` - Fetch data from API
- `handleFilterChange()` - Update filter state
- `clearFilters()` - Reset all filters
- `formatTimestamp()` - Format ISO dates
- `getStatusColor()` - Get color for status badges

### Sub-Components

#### GridView
Card-based layout showing lineage records in a responsive grid.

**Props:**
- `records` - Filtered records array
- `onSelectRecord` - Callback for record selection
- `formatTimestamp` - Date formatting function
- `getStatusColor` - Status color function

#### ListView
Table-based layout with sortable columns.

**Props:**
- `records` - Filtered records array
- `onSelectRecord` - Callback for record selection
- `formatTimestamp` - Date formatting function
- `formatDuration` - Duration formatting function
- `getStatusColor` - Status color function

#### TimelineView
Chronological timeline visualization with connection lines.

**Props:**
- `records` - Filtered records array (auto-sorted by timestamp)
- `onSelectRecord` - Callback for record selection
- `formatTimestamp` - Date formatting function
- `getStatusColor` - Status color function

#### DetailModal
Comprehensive modal showing all record details.

**Props:**
- `record` - Selected record object
- `onClose` - Callback to close modal
- `formatTimestamp` - Date formatting function
- `formatDuration` - Duration formatting function
- `getStatusColor` - Status color function

**Sections:**
- Overview - Run ID, status, timestamp, duration
- Lineage Info - Job ID, branch, parent
- Assets - List with checksums and metrics
- Validations - Scores and pass/fail status
- Rejections - Failed assets with reasons and suggestions
- System Info - Platform, architecture, memory usage

---

## Filtering & Search

### Available Filters

1. **Search Term** - Free text search
   - Searches in: Run ID, Job ID
   - Case-insensitive
   - Real-time filtering

2. **Job ID** - Dropdown filter
   - Auto-populated from records
   - Shows only records for selected job

3. **Branch** - Dropdown filter
   - Auto-populated from records
   - Filter by lineage branch

4. **Status** - Dropdown filter
   - Options: completed, failed, running
   - Filter by execution status

### Filter Combinations

Filters work together (AND logic):
```
Records WHERE
  (searchTerm matches) AND
  (jobId matches OR jobId filter empty) AND
  (branch matches OR branch filter empty) AND
  (status matches OR status filter empty)
```

---

## Statistics Dashboard

Real-time statistics calculated from filtered records:

| Metric | Description |
|--------|-------------|
| **Total Runs** | Number of lineage records |
| **Completed** | Successfully completed runs |
| **Failed** | Failed runs with errors |
| **Total Assets** | Sum of all generated assets |
| **Avg Score** | Average validation score (0-1) |
| **Avg Duration** | Average execution time |

---

## Styling & Customization

### CSS Classes

All styles are scoped with `.lineage-viewer` prefix to avoid conflicts.

**Main Classes:**
- `.lineage-viewer` - Root container
- `.lineage-header` - Header section
- `.statistics-bar` - Statistics cards container
- `.stat-card` - Individual statistic card
- `.filters-section` - Filters container
- `.grid-view` - Grid layout container
- `.list-view` - Table layout container
- `.timeline-view` - Timeline layout container
- `.modal-overlay` - Modal backdrop
- `.modal-content` - Modal content container

### Customization

Override styles in your own CSS:

```css
/* Custom primary color */
.lineage-viewer .stat-card {
  background: linear-gradient(135deg, #your-color 0%, #your-color-2 100%);
}

/* Custom card hover effect */
.lineage-viewer .record-card:hover {
  transform: scale(1.05);
}

/* Custom status badge colors */
.lineage-viewer .status-badge {
  background-color: var(--your-status-color);
}
```

### CSS Variables

Define custom properties for theming:

```css
:root {
  --lineage-primary: #3b82f6;
  --lineage-success: #10b981;
  --lineage-error: #ef4444;
  --lineage-warning: #f59e0b;
  --lineage-gray: #6b7280;
}
```

---

## Responsive Design

The component is fully responsive with breakpoints:

**Desktop (> 768px):**
- Grid: 3-4 columns
- Filters: Single row layout
- Statistics: 6 columns

**Tablet (768px - 1024px):**
- Grid: 2 columns
- Filters: 2 row layout
- Statistics: 3 columns

**Mobile (< 768px):**
- Grid: 1 column (stacked)
- Filters: Stacked vertically
- Statistics: 2 columns
- Table: Horizontal scroll

---

## Performance Optimization

### useMemo Hooks

The component uses `useMemo` for expensive calculations:

1. **filteredRecords** - Memoized filtered list
2. **filterOptions** - Memoized unique filter values
3. **statistics** - Memoized statistics calculations

### Lazy Loading

Sub-components are rendered conditionally based on view mode:
```javascript
{viewMode === 'grid' && <GridView ... />}
{viewMode === 'list' && <ListView ... />}
{viewMode === 'timeline' && <TimelineView ... />}
```

### API Optimization

- Filters trigger new API requests only for server-side filters (jobId, branch, status)
- Search term filters locally without API calls
- Records are cached in component state

---

## Error Handling

### Loading State

Displays spinner and loading message:
```jsx
<div className="lineage-viewer loading">
  <div className="spinner"></div>
  <p>Loading lineage records...</p>
</div>
```

### Error State

Shows error message with retry button:
```jsx
<div className="lineage-viewer error">
  <h3>❌ Error Loading Lineage</h3>
  <p>{error}</p>
  <button onClick={() => window.location.reload()}>Retry</button>
</div>
```

### Empty State

Friendly message when no records found:
```jsx
<div className="empty-state">
  <p>No lineage records found matching your filters.</p>
</div>
```

---

## Testing the Component

### 1. Start API Server

```bash
# Terminal 1: Start VaultMind Forge API
cd C:\Users\Administrator\Desktop\Projects\LPG
npm start
```

### 2. Generate Sample Lineage Data

```bash
# Terminal 2: Run generation with lineage
curl -X POST http://localhost:3000/api/diffusion/generate-with-lineage \
  -H "Content-Type: application/json" \
  -d '{
    "jobConfig": {
      "id": "test-job-1",
      "output_type": "character",
      "style_tags": ["anime", "cel-shaded"],
      "passes": 3,
      "lineage": { "branch": "main" }
    },
    "multiPass": true,
    "passes": 3,
    "packageAssets": true
  }'
```

### 3. View in Browser

**Option A: Standalone Demo**
```bash
# Open examples/lineage-viewer-demo.html in browser
start examples/lineage-viewer-demo.html
```

**Option B: React Dev Server**
```bash
# In your React project
npm run dev
```

---

## Integration Examples

### Example 1: Next.js App

```javascript
// pages/lineage.js
import LineageViewer from '../components/LineageViewer';

export default function LineagePage() {
  return (
    <div>
      <h1>Lineage Viewer</h1>
      <LineageViewer apiBaseUrl={process.env.NEXT_PUBLIC_API_URL} />
    </div>
  );
}
```

### Example 2: Create React App

```javascript
// src/App.js
import React from 'react';
import LineageViewer from './components/LineageViewer';
import './components/LineageViewer.css';

function App() {
  return (
    <div className="App">
      <LineageViewer />
    </div>
  );
}

export default App;
```

### Example 3: Vite React App

```javascript
// src/App.jsx
import { useState } from 'react';
import LineageViewer from './components/LineageViewer';
import './components/LineageViewer.css';

function App() {
  const [apiUrl, setApiUrl] = useState('http://localhost:3000/api');

  return (
    <div>
      <input
        type="text"
        value={apiUrl}
        onChange={(e) => setApiUrl(e.target.value)}
        placeholder="API URL"
      />
      <LineageViewer apiBaseUrl={apiUrl} />
    </div>
  );
}

export default App;
```

---

## Troubleshooting

### Component Not Loading

**Issue:** Blank screen or loading forever

**Solutions:**
1. Check API server is running: `curl http://localhost:3000/api/lineage`
2. Check browser console for errors
3. Verify CORS is enabled on API server
4. Check network tab for failed requests

### No Records Displayed

**Issue:** Empty state shown but records exist

**Solutions:**
1. Check API response format matches expected structure
2. Verify `data.records` array exists in response
3. Check browser console for parsing errors
4. Clear all filters and try again

### Styling Issues

**Issue:** Component looks broken or unstyled

**Solutions:**
1. Ensure CSS file is imported
2. Check for CSS conflicts with global styles
3. Verify CSS class names match
4. Clear browser cache

### CORS Errors

**Issue:** API requests blocked by CORS policy

**Solutions:**
1. Enable CORS on API server
2. Add CORS middleware in Express:
```javascript
import cors from 'cors';
app.use(cors({ origin: '*' }));
```

---

## Future Enhancements

Potential improvements for future versions:

- [ ] Export lineage data to JSON/CSV
- [ ] Compare multiple lineage records side-by-side
- [ ] Interactive charts for score trends
- [ ] Asset thumbnails preview
- [ ] Real-time updates with WebSocket
- [ ] Pagination for large datasets
- [ ] Advanced search with regex support
- [ ] Bookmark favorite records
- [ ] Share lineage records via URL
- [ ] Dark mode support

---

## Component API Reference

### Main Component

```typescript
interface LineageViewerProps {
  apiBaseUrl?: string;
}

interface LineageRecord {
  run_id: string;
  timestamp: string;
  lineage: {
    lineage_id: string;
    job_id: string;
    branch: string;
    parent: string | null;
  };
  job: {
    id: string;
    output_type: string;
    style_tags?: string[];
  };
  assets: Asset[];
  validations: Validation[];
  rejections?: Rejection[];
  execution: {
    start_time: string;
    end_time: string;
    duration_ms: number;
    status: 'completed' | 'failed' | 'running' | 'pending';
  };
  system: {
    platform: string;
    arch: string;
    node_version: string;
    memory_used_mb: number;
  };
}

interface Asset {
  asset_path: string;
  asset_name: string;
  checksum: string;
  validated: boolean;
  metrics?: {
    score: number;
  };
}

interface Validation {
  file: string;
  score: number;
  status: 'PASS' | 'FAIL';
  passed: boolean;
}

interface Rejection {
  asset_path: string;
  reason: string;
  validation_score: number;
  failed_metrics: string[];
  suggestions: string[];
}
```

---

## Summary

The **LineageViewer** component provides a complete solution for visualizing VaultMind Forge lineage records with:

- ✅ 3 view modes (Grid, List, Timeline)
- ✅ Advanced filtering and search
- ✅ Detailed record inspection
- ✅ Real-time statistics
- ✅ Responsive design
- ✅ Rejection analysis with suggestions
- ✅ System information display
- ✅ Performance optimized
- ✅ Easy integration
- ✅ Fully documented

**Total Code: ~750 lines React + 400 lines CSS**

Ready for production use! 🎉
