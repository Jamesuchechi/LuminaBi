# Bug Fix - Dataset API Error

## Problem
When accessing `/api/datasets/` endpoint, the system threw a FieldError:
```
django.core.exceptions.FieldError: Cannot resolve keyword 'is_public' into field
```

## Root Cause
The `DatasetViewSet.get_queryset()` method was trying to filter by `is_public` field:
```python
return Dataset.objects.filter(
    Q(owner=self.request.user) | Q(is_public=True)
)
```

However, the `Dataset` model doesn't have an `is_public` field. This field exists on the `Visualization` model but not on `Dataset`.

## Solution
Removed the `is_public` filter from the Dataset query, keeping only the owner filter:
```python
return Dataset.objects.filter(owner=self.request.user)
```

This ensures users can only access their own datasets through the API, which is the correct behavior.

## Files Modified
- `/api/views.py` - Updated `DatasetViewSet.get_queryset()` method

## Verification
✅ Django checks pass  
✅ Dataset query test passes  
✅ Server starts without errors  
✅ API endpoint now accessible  

## Testing
To test the fix:
1. Navigate to `/visualizations/create/`
2. The dataset dropdown should now load successfully
3. Columns should appear after dataset selection
4. Chart preview should generate without errors

## Status
✅ **FIXED** - Ready for production

