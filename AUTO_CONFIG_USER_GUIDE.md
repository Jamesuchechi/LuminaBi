# Automatic Chart Configuration System - User Guide

## Overview

The LuminaBi visualization system now includes **automatic JSON chart configuration generation**. When you select a dataset to visualize, the system intelligently analyzes your data and creates an appropriate chart configuration automatically.

### What This Means
- **No More Placeholders**: Real charts display immediately after selection
- **No Manual JSON**: The system generates Chart.js configuration automatically
- **Smart Defaults**: Optimal chart type chosen based on your data structure
- **Still Customizable**: You can edit the configuration manually if needed

---

## Quick Start Guide

### Creating a Visualization with Auto-Config

#### Step 1: Upload Your Data
1. Navigate to **Datasets** → **Upload**
2. Select your CSV, Excel, or JSON file
3. System analyzes the data automatically

#### Step 2: Create Visualization
1. Go to **Visualizations** → **Create**
2. Fill in the form:
   - **Title**: Give your visualization a name
   - **Description**: Optional description
   - **Chart Type**: Choose your preferred chart type
   - **Dataset**: Select your uploaded dataset

#### Step 3: Auto-Generate Configuration
**Option A: Automatic (on save)**
- Leave the **Config** field empty
- Click **Create Visualization**
- System generates config automatically

**Option B: Manual trigger**
- Select your dataset
- Click the **Auto Config** button (green button with wand icon)
- Config field populates with generated JSON
- Click **Create Visualization**

#### Step 4: View Your Chart
- Chart renders automatically with real data
- No placeholders or icons
- Fully interactive visualization

---

## Understanding Chart Type Selection

### Automatic Detection
The system recommends chart types based on your data:

| Data Pattern | Recommended Chart | Why |
|---|---|---|
| Many categories + numbers | Bar | Easy comparison |
| Time series / trends | Line | Shows progression |
| ≤10 categories | Pie/Donut | Part-to-whole |
| Two numeric columns | Scatter | Correlation |
| Many numeric columns | Area | Cumulative view |
| Multiple dimensions | Radar | Multi-variate |
| 3D relationships | Bubble | Size dimension |

### Manual Selection
You can override auto-detection:
1. Select any chart type from dropdown
2. Choose your dataset
3. Click **Auto Config** or save
4. System generates config for selected type

---

## Supported Chart Types

### 1. **Bar Chart**
- **Best for**: Comparing values across categories
- **Example**: Sales by region, product performance
- **Data needed**: 1 categorical column, 1+ numeric columns

### 2. **Line Chart**
- **Best for**: Trends over time
- **Example**: Temperature over months, stock prices
- **Data needed**: Time/sequential column, 1+ numeric values

### 3. **Pie Chart**
- **Best for**: Part-to-whole relationships
- **Best with**: ≤10 categories
- **Example**: Market share, budget allocation
- **Data needed**: 1 categorical column, 1 numeric value

### 4. **Scatter Plot**
- **Best for**: Correlation between two variables
- **Example**: Height vs weight, hours studied vs grades
- **Data needed**: 2 numeric columns

### 5. **Area Chart**
- **Best for**: Cumulative trends
- **Example**: Stacked revenue over time
- **Data needed**: Time/sequential column, 1+ numeric values

### 6. **Radar Chart**
- **Best for**: Multi-variate analysis
- **Example**: Skills comparison, performance metrics
- **Data needed**: Categories and multiple numeric values

### 7. **Bubble Chart**
- **Best for**: 3-dimensional relationships
- **Example**: GDP vs population vs growth rate
- **Data needed**: 3 numeric columns

### 8. **Donut Chart**
- **Best for**: Part-to-whole (styled pie)
- **Example**: Browser usage, device breakdown
- **Data needed**: 1 categorical column, 1 numeric value

### 9. **Heatmap**
- **Best for**: 2D data matrix
- **Example**: Correlation matrix, time-of-day analysis
- **Data needed**: 2D numeric data

### 10. **Treemap**
- **Best for**: Hierarchical data
- **Example**: Disk space usage, org structure
- **Data needed**: Hierarchical categories with values

---

## Configuration Details

### What Gets Generated

When you auto-generate config, the system creates:

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
        "borderColor": "rgba(0, 243, 255, 0.8)",
        "borderWidth": 2
      }
    ]
  },
  "options": {
    "responsive": true,
    "maintainAspectRatio": false,
    "plugins": {
      "title": {
        "display": true,
        "text": "Your Chart Title",
        "font": {"size": 16, "weight": "bold"}
      }
    }
  }
}
```

### Color Scheme

All charts use a consistent dark theme with neon colors:
- **Primary Colors**: Cyan, Purple, Pink, Green, Orange, Red
- **Background**: Dark with transparency
- **Text**: White for contrast
- **Grid**: Subtle white lines

---

## Advanced Features

### API Endpoints

#### Generate Config via API
```
POST /api/visualizations/{id}/generate_config/
```

Response:
```json
{
  "status": "success",
  "message": "Configuration generated successfully",
  "config": {...},
  "chart_type": "bar"
}
```

#### Update Config Manually
```
POST /api/visualizations/{id}/update_config/
Body: {"config": {...}}
```

---

## Troubleshooting

### "No Dataset Linked"
- **Problem**: You tried auto-generating without selecting a dataset
- **Solution**: Select a dataset from the dropdown first

### "Configuration Generation Failed"
- **Problem**: System couldn't read or parse the dataset
- **Solution**: 
  - Check dataset file format (CSV, Excel, JSON)
  - Ensure file isn't corrupted
  - Try uploading a new dataset
  - Manually enter configuration as fallback

### Chart Shows Placeholder Icons
- **Problem**: Config wasn't generated or is invalid
- **Solution**:
  - Click "Auto Config" button to regenerate
  - Or manually enter valid Chart.js config
  - Check browser console for errors

### Wrong Chart Type Generated
- **Problem**: Auto-detection chose unexpected type
- **Solution**:
  1. Select desired chart type from dropdown
  2. Keep dataset selection
  3. Click "Auto Config"
  4. System regenerates for selected type

---

## Best Practices

### ✅ Do's
- ✅ Clean your data before uploading
- ✅ Use descriptive column names
- ✅ Keep categorical values consistent
- ✅ Try different chart types for comparison
- ✅ Use meaningful titles

### ❌ Don'ts
- ❌ Don't upload corrupted files
- ❌ Don't expect perfect charts automatically (review and adjust)
- ❌ Don't use extreme data ranges (normalize if needed)
- ❌ Don't ignore error messages

---

## Examples

### Example 1: Sales Dashboard

**Data:**
```
Region,Q1_Sales,Q2_Sales,Q3_Sales
North,50000,55000,62000
South,45000,48000,52000
East,60000,65000,70000
West,48000,52000,58000
```

**Steps:**
1. Upload as CSV
2. Create Visualization
3. Select "Bar" chart type
4. Select the dataset
5. Click Auto Config
6. View grouped bar chart showing quarterly comparison

---

### Example 2: Website Traffic Trends

**Data:**
```
Date,Desktop,Mobile,Tablet
2024-01-01,1000,2000,500
2024-01-02,1100,2100,550
2024-01-03,1050,2050,520
```

**Steps:**
1. Upload as CSV
2. Create Visualization
3. Select "Line" chart type
4. Auto-config generates multi-line chart
5. View trend over time with legend

---

### Example 3: Market Share

**Data:**
```
Company,MarketShare
Apple,25
Samsung,20
Nokia,15
Others,40
```

**Steps:**
1. Upload as CSV
2. Create Visualization
3. Select "Pie" chart type
4. Auto-config generates pie chart
5. View proportional representation

---

## Performance Notes

- Auto-generation is fast for datasets with <10k rows
- Large datasets (>100k rows) may take a few seconds
- Charts remain responsive even with 1000+ data points
- Configuration is cached after generation

---

## Support

For issues or feature requests related to auto-configuration:
1. Check this guide
2. Review error messages carefully
3. Verify dataset format
4. Try different chart types
5. Contact support if persistent issues occur

---

**Happy Visualizing! 📊**
