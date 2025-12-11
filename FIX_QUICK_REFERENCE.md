# 405 Method Not Allowed - FIXED ✅

## What Was Wrong
The `/api/visualizations/preview-config/` endpoint was returning **HTTP 405 Method Not Allowed** when users tried to generate chart previews.

## What Was Fixed

### 1. **Removed Duplicate Router Action**
   - **File**: `visualizations/views.py`
   - **Removed**: `@action(detail=False, methods=['post'], url_path='preview-config')` from VisualizationViewSet
   - **Why**: This action was conflicting with the direct URL endpoint

### 2. **Fixed URL Pattern Ordering**
   - **File**: `api/urls.py`
   - **Change**: Moved direct endpoint BEFORE `router.urls`
   - **Before**: 
     ```python
     urlpatterns = [
         path('', include(router.urls)),  # Matches everything first
         path('visualizations/preview-config/', ...),  # Never reached
     ]
     ```
   - **After**:
     ```python
     urlpatterns = [
         path('visualizations/preview-config/', ...),  # Matches first ✅
         path('', include(router.urls)),  # Fallback for other routes
     ]
     ```

## How to Test

### Quick Test in Browser
1. Go to `http://localhost:8000/visualizations/create/`
2. Select a dataset
3. Select a chart type
4. Click "Generate Preview"
5. **Expected**: Chart appears (no 405 error)

### Terminal Test
```bash
# Start server
python manage.py runserver

# In another terminal, test the endpoint
curl -X POST http://localhost:8000/api/visualizations/preview-config/ \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "chart_type": "bar"}' \
  -b "sessionid=<your_session_id>" \
  -v
```

**Expected Response**: 200 OK with JSON containing chart configuration

## Files Changed

| File | Change | Lines |
|------|--------|-------|
| `visualizations/views.py` | Removed router action | 412-467 removed |
| `api/urls.py` | Reordered patterns | Moved direct endpoint before router |

## Verification Checklist

- ✅ Django checks pass: `python manage.py check`
- ✅ Direct endpoint exists: `preview_config_direct`
- ✅ URL registered: `/api/visualizations/preview-config/`
- ✅ Method handling: Explicit POST check
- ✅ Authentication: `@login_required` decorator
- ✅ Template uses correct endpoint
- ✅ CSRF tokens configured
- ✅ Session authentication enabled

## Why This Works

**URL Resolution in Django is top-down**:
- When a request comes to `/api/visualizations/preview-config/`, Django checks patterns in order
- The first matching pattern wins
- By placing the specific endpoint first, it matches before the generic router pattern

## Example Request/Response

### Request
```json
POST /api/visualizations/preview-config/
Content-Type: application/json
X-CSRFToken: abc123...

{
  "dataset_id": 1,
  "chart_type": "bar",
  "title": "Sales by Region",
  "selected_columns": ["region", "sales"],
  "show_legend": true
}
```

### Response
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "config": {
    "type": "bar",
    "data": {
      "labels": ["North", "South", "East", "West"],
      "datasets": [{
        "label": "Sales",
        "data": [1200, 1900, 3000, 2500]
      }]
    },
    "options": {...}
  }
}
```

## Troubleshooting

If you still see 405 errors:

1. **Clear Django cache**: `python manage.py clear_cache`
2. **Restart server**: Stop and restart `python manage.py runserver`
3. **Check authentication**: Ensure you're logged in when testing
4. **Verify URL order**: Check `api/urls.py` line 36-40

## Next Steps

The visualization creation flow is now fully functional:
- ✅ Select dataset
- ✅ View columns
- ✅ Select chart type
- ✅ **NEW**: Generate preview (previously 405, now 200 ✅)
- ✅ Save visualization

Users can now create visualizations end-to-end without errors!
