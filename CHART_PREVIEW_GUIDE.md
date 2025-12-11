## Chart Preview & Auto-Generation System - Complete Guide

### Overview

This system provides **instant chart preview** and **automatic JSON configuration generation** for visualizations. Users can now see real charts during creation and don't need to save to preview.

---

## What Changed

### 1. **Form Page** (Create/Edit Visualization)

#### Old Experience:
- Fill form
- Manually write JSON or leave blank
- Save
- Go to detail page
- See placeholder or broken chart
- Edit and try again

#### New Experience:
- Fill form with title and chart type
- Select a dataset
- Click "Preview" button
- **Instantly see the real chart in a live preview panel**
- Satisfied? Click Save
- Done!

#### Layout:
- **Left side**: Form fields (title, dataset, chart type, config)
- **Right side**: Live chart preview that updates in real-time
- **Sticky**: Preview panel stays visible while scrolling

---

## How to Use

### Creating a Visualization

#### Step 1: Access Create Page
```
Navigate to: Visualizations → Create
```

#### Step 2: Fill Basic Information
- **Title**: "Sales by Region"
- **Description**: (optional)
- **Chart Type**: Select from dropdown (Bar, Line, Pie, etc.)

#### Step 3: Select Your Data
- **Dataset**: Select from your uploaded datasets
- Once selected, a green "Preview" button appears

#### Step 4: Generate & Preview
- **Click the green "Preview" button**
- Wait for generation (usually <1 second)
- **Real chart appears in the preview panel**
- Status shows: "✓ Config auto-generated successfully"
- JSON config populates automatically

#### Step 5: Save
- Review the chart
- Click "Save Visualization"
- Chart is created and ready to view!

#### Step 6: View Full Chart
- Redirected to visualization detail page
- **Full interactive chart is displayed**
- Can still edit and regenerate if needed

---

## Features

### ✨ Live Preview
- Real-time chart rendering
- Uses Chart.js for interactive visualizations
- Updates as you make changes
- Shows loading state during generation

### ⚡ Instant Generation
- No need to save to see results
- Generates config immediately on button click
- Works with all 10 chart types
- Smart defaults based on data

### 🎨 Beautiful UI
- 2-column responsive layout
- Dark theme matching the platform
- Smooth animations and transitions
- Clear error messages

### 🔄 Smart Defaults
- Automatically detects best chart type
- Uses optimal column mapping
- Applies consistent styling
- Handles edge cases gracefully

### 🛡️ Error Handling
- Permission checking
- File existence validation
- Parse error handling
- User-friendly error messages
- Fallback UI for missing data

---

## Chart Types Supported

| Chart Type | Best For | Example |
|---|---|---|
| **Bar** | Comparing categories | Sales by region |
| **Line** | Trends over time | Stock prices |
| **Pie** | Part-to-whole (≤10) | Market share |
| **Scatter** | Correlations | Height vs Weight |
| **Area** | Cumulative trends | Revenue growth |
| **Radar** | Multi-variate data | Skills matrix |
| **Bubble** | 3D relationships | GDP vs Population |
| **Donut** | Part-to-whole styled | Budget allocation |
| **Heatmap** | 2D matrices | Correlation table |
| **Treemap** | Hierarchical data | Org structure |

---

## API Endpoints

### Generate Preview Config
```
POST /api/visualizations/preview_config/
```

**Purpose**: Generate chart config without saving visualization (for live preview)

**Request Body**:
```json
{
    "dataset_id": 123,
    "chart_type": "bar",
    "title": "Sales Chart"
}
```

**Response (Success)**:
```json
{
    "status": "success",
    "config": {
        "type": "bar",
        "data": {...},
        "options": {...}
    },
    "chart_type": "bar"
}
```

**Response (Error)**:
```json
{
    "error": "Error message describing what went wrong"
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Missing required field
- `404`: Dataset not found
- `500`: Generation error

### Generate & Save Config
```
POST /api/visualizations/{id}/generate_config/
```

**Purpose**: Generate config for existing visualization and save it

**Permission**: Own the visualization

---

## Technical Details

### Configuration Structure

Generated configs follow Chart.js format:

```json
{
    "type": "bar",
    "data": {
        "labels": ["Jan", "Feb", "Mar"],
        "datasets": [
            {
                "label": "Sales",
                "data": [100, 150, 120],
                "backgroundColor": "#00f3ff",
                "borderColor": "rgba(0, 243, 255, 0.8)"
            }
        ]
    },
    "options": {
        "responsive": true,
        "maintainAspectRatio": false,
        "plugins": {
            "title": {
                "display": true,
                "text": "Sales Chart"
            }
        },
        "scales": {
            "x": {...},
            "y": {...}
        }
    }
}
```

### Color Scheme

- **Primary**: Cyan, Purple, Pink, Green
- **Background**: Dark with transparency
- **Grid**: Subtle white lines
- **Text**: White for contrast

### Performance

- Config generation: <1 second for typical datasets
- Chart rendering: Immediate
- No database overhead
- Cached properly for subsequent views
- Lightweight Chart.js library

---

## Troubleshooting

### Preview Button Doesn't Appear
**Problem**: No dataset selected
**Solution**: Select a dataset from the dropdown first

### "Failed to Generate Configuration" Error
**Problem**: Dataset file not found or corrupted
**Solutions**:
- Verify dataset still exists
- Check file isn't corrupted
- Try uploading a new dataset
- Check console for more details

### Chart Shows Placeholder
**Problem**: Config not generated or invalid
**Solutions**:
- Click Preview button again
- Check browser console for errors
- Verify dataset has valid data
- Try different chart type

### Chart Looks Wrong
**Problem**: Column mapping not what you expected
**Solutions**:
- Click Preview with different chart type
- Manually edit the JSON config
- Verify your dataset structure
- Check for missing/invalid values

### Different Data Than Expected
**Problem**: Dataset has been modified since creation
**Solutions**:
- Re-generate config with Preview button
- All charts update when viewing detail page
- Config is always based on current dataset

---

## Best Practices

### ✅ Do's
- ✅ Clean your data before visualizing
- ✅ Use descriptive column names
- ✅ Try different chart types to find best fit
- ✅ Preview before saving
- ✅ Use meaningful titles

### ❌ Don'ts
- ❌ Don't expect perfection - review and adjust
- ❌ Don't ignore error messages
- ❌ Don't use extremely large datasets (100k+ rows)
- ❌ Don't modify dataset after creating charts
- ❌ Don't use special characters in column names

---

## Examples

### Example 1: Bar Chart - Sales Data

**Step 1**: Upload CSV with columns: Region, Q1, Q2, Q3

**Step 2**: Create visualization
- Title: "Quarterly Sales"
- Chart Type: Bar
- Dataset: Select your CSV

**Step 3**: Click Preview
- Chart instantly shows grouped bars
- One bar per region, three bars (Q1-Q3)
- Color-coded and labeled

**Result**: Interactive chart comparing quarterly sales by region

---

### Example 2: Line Chart - Time Series

**Step 1**: Upload CSV with columns: Date, Value1, Value2

**Step 2**: Create visualization  
- Title: "Trends"
- Chart Type: Line
- Dataset: Select your CSV

**Step 3**: Click Preview
- Chart shows line graph with time on X-axis
- Two lines (Value1 and Value2)
- Legend showing both series

**Result**: Interactive line chart showing trends over time

---

### Example 3: Pie Chart - Market Share

**Step 1**: Upload CSV with columns: Company, MarketShare

**Step 2**: Create visualization
- Title: "Market Share"
- Chart Type: Pie
- Dataset: Select your CSV

**Step 3**: Click Preview
- Chart shows pie slices
- One slice per company
- Proportional to market share values

**Result**: Interactive pie chart showing proportions

---

## FAQ

**Q: Why does preview generation take a second sometimes?**
A: Depends on dataset size. Larger datasets need more processing. Usually <1 second.

**Q: Can I manually edit the config after previewing?**
A: Yes! The config field is editable. Make changes and save.

**Q: Will existing visualizations show charts now?**
A: Yes! All visualizations with configs will display as charts.

**Q: What if I don't have Chart.js installed?**
A: Already included via CDN - no installation needed.

**Q: Can I preview without a dataset?**
A: No, dataset is required to generate config from real data.

**Q: What happens if dataset is deleted?**
A: Chart still displays if config exists, but can't regenerate preview.

**Q: Can I use this API programmatically?**
A: Yes! POST to `/api/visualizations/preview_config/` from your app.

---

## Support

Having issues? 
1. Check this guide
2. Review error message carefully
3. Try with a different dataset
4. Check browser console (F12)
5. Contact support with details

---

**Happy Visualizing!** 📊✨
