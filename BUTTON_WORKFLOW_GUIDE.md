# Separate Generate & Preview Button Workflow

## Problem Fixed

The previous implementation had a "Method Not Allowed: 405" error on the `/api/visualizations/preview_config/` endpoint. This has been resolved and the workflow has been improved with separate buttons.

## New Workflow

### Two-Step Process

1. **Generate Button** (Blue)
   - Generates the chart configuration from the selected dataset
   - Populates the config JSON field automatically
   - Enables the Preview button once config is generated
   - Status: `✓ Config generated successfully`

2. **Preview Button** (Green)
   - Only enabled AFTER config is generated
   - Shows a live preview of the chart in the right panel
   - Allows testing different chart types without saving
   - Let's you verify the chart looks correct before saving

### User Flow

```
1. Select a dataset
   ↓
2. Click "Generate" button
   ↓
3. Config JSON field populates automatically
   ↓
4. "Preview" button becomes enabled
   ↓
5. Click "Preview" to see live chart
   ↓
6. Change chart type and click "Preview" again to test
   ↓
7. When satisfied, click "Save"
```

## Technical Changes

### API Endpoint

**Fixed URL**: `/api/visualizations/preview-config/` (note the hyphen, not underscore)

The endpoint now uses `@action(detail=False, methods=['post'], url_path='preview-config')` which properly registers with DRF's DefaultRouter.

**Request Parameters:**
```json
{
  "dataset_id": 123,
  "chart_type": "bar",
  "title": "My Chart"
}
```

**Response:**
```json
{
  "status": "success",
  "config": { /* Chart.js configuration object */ },
  "chart_type": "bar"
}
```

### Form Template Updates

#### HTML Changes
- Dataset field is now standalone (no button inline)
- Two separate buttons below:
  - **Generate** (Blue): Generates config from dataset
  - **Preview** (Green): Previews the chart (disabled until config generated)

#### JavaScript Functions

**`generateConfig()`**
- Called when "Generate" button is clicked
- Makes POST request to `/api/visualizations/preview-config/`
- Updates the config textarea with generated JSON
- Enables the Preview button
- Shows success status

**`generateAndPreviewChart()`**
- Called when "Preview" button is clicked
- Makes POST request to `/api/visualizations/preview-config/`
- Renders the chart in the right panel
- Shows live preview in real-time

**Button State Management**
- Generate button shows when dataset is selected
- Preview button only shows and is enabled after Generate is clicked
- Buttons hide when dataset is deselected
- Preview button resets when changing dataset

## Benefits

✅ **Clear Separation of Concerns**
- Generate = populate config
- Preview = view chart

✅ **Better User Feedback**
- Users know when config is ready
- Preview button disabled until ready

✅ **More Control**
- Can generate once, preview multiple times
- Can change chart type and preview again
- Confirms everything before saving

✅ **Error Clarity**
- Generate errors clearly shown
- Preview errors don't affect config
- Users can retry independently

## Testing Instructions

1. Go to create a new visualization
2. Fill in Title and Description
3. Select a Chart Type
4. **Select a Dataset** → "Generate" button appears (blue)
5. Click "Generate" → Config field populates with JSON
6. "Preview" button appears (green) and is enabled
7. Click "Preview" → Chart appears in right panel in real-time
8. Change the Chart Type dropdown
9. Click "Preview" again → New chart type previews instantly
10. When satisfied, click "Save"
11. Chart should display beautifully on the detail page

## Expected Result

✓ No more "Method Not Allowed" errors
✓ Config generates successfully
✓ Live chart preview appears
✓ Can test different chart types
✓ All changes work smoothly
✓ Save button stores the visualization with its config

## If Issues Occur

### Chart not appearing in preview:
- Check browser console (F12) for JavaScript errors
- Verify dataset has valid data
- Ensure chart type matches data (e.g., bar needs categories)

### Generate button not responding:
- Check that dataset is selected
- Verify CSRF token is present
- Check Network tab for API response

### Config field remains empty:
- Check API response in Network tab
- Verify dataset file exists
- Check server logs for errors

## API Response Errors

| Status | Message | Solution |
|--------|---------|----------|
| 400 | dataset_id is required | Select a dataset |
| 404 | Dataset not found | Verify dataset exists and you own it |
| 404 | Dataset file not found | Re-upload the dataset |
| 500 | Failed to generate preview | Check server logs, may be data format issue |

---

**Status**: ✅ Complete and Ready
**URL**: `/api/visualizations/preview-config/`
**Buttons**: Generate (blue) + Preview (green)
**Workflow**: Select → Generate → Preview → Save
