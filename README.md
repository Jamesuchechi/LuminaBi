
# 🌟 LuminaBI  
### A Django-Powered Automated Data Analytics & Business Intelligence Platform

LuminaBI is a modern, lightweight alternative to Power BI and Tableau — built with **Django**, **Pandas**, **Chart.js**, and **Django REST Framework**.  
It automatically transforms raw datasets into **clean data**, **visual dashboards**, and **actionable insights**, with no technical skills required.

---

## 🚀 Features

### 🔐 Authentication
- User registration & login  
- Password reset  
- Profile management  
- Secure session-based authentication  

### 📤 Dataset Upload
- Upload CSV, Excel, JSON, and PDF files 
- Automatic file validation and preview
- Metadata extraction (size, columns, rows, file type)  
- Real-time upload progress with WebSocket
- Raw & cleaned versions stored securely  

### 🧼 Automated Data Cleaning
- Intelligent duplicate detection and removal
- Handle missing values(Smart missing value handling (mean, median, mode, interpolation))  
- Column name normalization (snake_case, CamelCase, etc.)
- Convert datatype inconsistencies  
- Date/time parsing with multiple format detection
- Generate summary statistics  

### 📊 Auto-Generated Visualizations
- Bar, Line, Pie charts  
- Correlation heatmaps  
- Auto-chart suggestions based on data types
- Histograms  
- Scatter plots  
- Real-time chart updates with WebSocket
- Smart chart suggestions based on column types  
- Visualizations rendered with **Chart.js / Plotly.js**  

### 🧠 Insights Engine
- Trend detection and analysis  
- Category rankings  
- Outlier identification with statistical methods
- Correlation analysis and heatmaps 
- Time-series summaries  
- AI-powered insights  

### 📉 Dashboard Builder
    Drag-and-drop interface with HTML5 Drag API

    Grid-based layout system

    Real-time collaboration with WebSocket

    Multiple saved dashboards per user

    Interactive filters (date ranges, categories, sliders)

    Public shareable dashboard links

### 📄 Exporting & Reporting
- PDF report generation  
- Export cleaned dataset  
- Export charts as PNG  
- Public shareable dashboard links  
- email report delivery
- scheduled automated delivery

### 🧩 REST API (Optional)
- Upload dataset  
- Fetch clean dataset  
- Retrieve analytics JSON  
- Chart config endpoints  
- Token-based authentication  

---

# 🏗️ Tech Stack

### **Backend**
- Django  
- Django REST Framework  
- Pandas / NumPy  
- Scikit-learn (optional insights)  
- PostgreSQL  

### **Frontend**
- HTML5 / TailwindCSS  
- Chart.js or Plotly  
- HTMX / Alpine.js  
- AJAX for dynamic updates  

### **DevOps**
- Docker (optional)  
- Gunicorn + Nginx (deployment)  

---

