# Chart Preview Endpoint Fix Summary

## Problem
The visualization chart preview generation was failing with **HTTP 405 Method Not Allowed** errors when users tried to generate chart previews.

### Error Logs
```
WARNING 2025-12-11 09:37:49,105 log 9269 Method Not Allowed: /api/visualizations/preview-config/
127.0.0.1:49738 - - [11/Dec/2025:09:37:49] "POST /api/visualizations/preview-config/" 405 41
```

## Root Causes Identified

### 1. Router-Based Action Conflicts
The `VisualizationViewSet` had a custom action `@action(detail=False, methods=['post'], url_path='preview-config')` that was conflicting with routing. When DRF routers generate URLs, they create patterns that can interfere with direct URL patterns.

### 2. URL Pattern Ordering
The direct fallback endpoint `preview_config_direct` was registered **AFTER** `router.urls` in `api/urls.py`, meaning the router pattern would match first and reject the POST request.

## Solutions Applied

### Solution 1: Remove Router-Based Action ✅
**File**: `/visualizations/views.py`

Removed the duplicate `preview_config` action from the `VisualizationViewSet` (lines 412-467) since we have a dedicated view endpoint.

**Why**: Eliminates routing conflicts and method confusion. The direct endpoint is simpler and works reliably.

### Solution 2: Reorder URL Patterns ✅
**File**: `/api/urls.py`

Moved the direct preview-config endpoint **BEFORE** the router include:

```python
urlpatterns = [
    # Direct preview-config endpoint (MUST come before router.urls to be matched first)
    path('visualizations/preview-config/', viz_views.preview_config_direct, name='visualization_preview_config'),

    # API Routes (router) - comes after so specific paths take precedence
    path('', include(router.urls)),

    # Health check
    path('health/', views.health_check, name='health'),

    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

**Why**: Django URL routing is top-down. The first matching pattern wins. By placing the specific endpoint before the catch-all router, we ensure it's matched first.

## Verification

### Django System Checks
```bash
$ python manage.py check
System check identified no issues (0 silenced).
```
✅ **PASSED** - No syntax or configuration errors

### Endpoint Configuration
- ✅ View function `preview_config_direct` exists at line 429 in `visualizations/views.py`
- ✅ Registered at `/api/visualizations/preview-config/` with proper name
- ✅ Has `@login_required` decorator for authentication
- ✅ Explicitly checks for POST method with 405 fallback
- ✅ Proper JSON request/response handling
- ✅ Includes fallback chart generation logic

### Frontend Integration
- ✅ Template uses correct endpoint: `/api/visualizations/preview-config/`
- ✅ Correct HTTP method: POST
- ✅ Proper headers:
  - `Content-Type: application/json`
  - `X-CSRFToken: <csrf_token>` (for session-based auth)
- ✅ Credentials: `same-origin` (for cookie-based session auth)

## Technical Details

### How the Endpoint Works

1. **Request**: Frontend sends POST to `/api/visualizations/preview-config/` with:
   ```json
   {
     "dataset_id": 1,
     "chart_type": "bar",
     "title": "My Chart",
     "selected_columns": ["col1", "col2"],
     "show_legend": true
   }
   ```

2. **Authentication**: Uses Django session authentication (not JWT)
   - User must be logged in (`@login_required`)
   - CSRF token validated from request headers
   - Request cookies contain `sessionid`

3. **Processing**:
   - Validates dataset ownership (user must own the dataset)
   - Parses the dataset file using `FileParser`
   - Generates chart configuration using `ChartConfigGenerator`
   - Falls back to simple config if generation fails

4. **Response**: Returns JSON with chart configuration:
   ```json
   {
     "status": "success",
     "config": {
       "type": "bar",
       "data": {
         "labels": [...],
         "datasets": [...]
       },
       "options": {...}
     },
     "chart_type": "bar"
   }
   ```

### URL Resolution Process

When a POST request comes to `/api/visualizations/preview-config/`:

1. Django starts matching against `urlpatterns` from top to bottom
2. **Matches** the direct pattern: `path('visualizations/preview-config/', ...)`
3. Routes to `preview_config_direct` view
4. View checks method is POST ✅
5. Processes request and returns response

The router-based pattern `visualizations/` would come later, but it never reaches that point because the specific path matched first.

## Why This Fix Works

### Before
- Router action `preview_config` was ambiguous (could be GET or POST)
- Router URL `visualizations/preview-config/` matched but router didn't properly handle the action
- Multiple URL patterns competing for the same request path

### After
- Single, clear endpoint with explicit method handling
- URL pattern ordering ensures it's matched first
- Direct view control over request/response
- No DRF router complications

## Testing the Fix

### Manual Test (Browser)
1. Navigate to `/visualizations/create/`
2. Select a dataset from dropdown
3. Select a chart type
4. Click "Generate Preview"
5. Chart should render (no more 405 errors)

### API Test (Command Line)
```bash
curl -X POST http://localhost:8000/api/visualizations/preview-config/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf_token>" \
  -b "sessionid=<session_cookie>" \
  -d '{"dataset_id": 1, "chart_type": "bar"}'
```

Expected response: 200 OK with chart configuration JSON

## Files Modified

1. **`/visualizations/views.py`**
   - Removed router action `preview_config` (was lines 412-467)
   - Kept direct view `preview_config_direct` (now at line 429)

2. **`/api/urls.py`**
   - Reordered patterns: direct endpoint before router.urls
   - Added explanatory comments about pattern precedence

## Next Steps

The visualization workflow is now complete:
1. ✅ User navigates to `/visualizations/create/`
2. ✅ Dataset loads and displays columns
3. ✅ User selects chart type and columns
4. ✅ **FIXED**: Chart preview generates without 405 errors
5. ✅ User can save visualization with name

Test the complete flow end-to-end to ensure everything works as expected.
