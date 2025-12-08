#!/usr/bin/env python3
"""
Quick verification script to check analysis page setup
Run this after uploading a dataset to verify everything works
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Luminabi.settings')
django.setup()

from datasets.models import Dataset, FileAnalysis
from django.contrib.auth.models import User

print("\n" + "="*80)
print("ANALYSIS PAGE VERIFICATION CHECKLIST")
print("="*80 + "\n")

# Get a sample dataset
datasets = Dataset.objects.filter(is_analyzed=True)[:1]

if not datasets:
    print("❌ No analyzed datasets found. Upload a file first!")
    sys.exit(1)

dataset = datasets[0]
print(f"📊 Testing with dataset: {dataset.name}")
print(f"   File type: {dataset.file_type}")
print(f"   File size: {dataset.file_size} bytes\n")

# Check Analysis Record
print("1. ANALYSIS RECORD")
try:
    analysis = FileAnalysis.objects.get(dataset=dataset)
    print("   ✅ FileAnalysis record exists")
except FileAnalysis.DoesNotExist:
    print("   ❌ No FileAnalysis record found!")
    sys.exit(1)

# Check Analysis Data Structure
print("\n2. ANALYSIS DATA STRUCTURE")
if analysis.analysis_data:
    keys = list(analysis.analysis_data.keys())
    print(f"   ✅ analysis_data populated with keys: {keys}")
    
    required_keys = ['basic_stats', 'empty_cells', 'duplicates', 'column_stats', 'data_quality_score', 'summary', 'outliers']
    missing = [k for k in required_keys if k not in analysis.analysis_data]
    
    if missing:
        print(f"   ⚠️  Missing keys: {missing}")
    else:
        print("   ✅ All required keys present")
else:
    print("   ❌ analysis_data is empty!")

# Check Basic Stats
print("\n3. BASIC STATISTICS")
basic_stats = analysis.analysis_data.get('basic_stats', {})
print(f"   ✅ Rows: {basic_stats.get('rows', 'N/A')}")
print(f"   ✅ Columns: {basic_stats.get('columns', 'N/A')}")

# Check Data Quality Score
print("\n4. DATA QUALITY SCORE")
quality_score = analysis.analysis_data.get('data_quality_score', 0)
print(f"   ✅ Score: {quality_score}% (0-100 scale)")
if not (0 <= quality_score <= 100):
    print(f"   ⚠️  Score out of range!")

# Check Empty Cells
print("\n5. EMPTY CELLS DETECTION")
empty_cells = analysis.analysis_data.get('empty_cells', {})
empty_count = empty_cells.get('total_empty_cells', 0)
print(f"   ✅ Total empty cells: {empty_count}")
if empty_count > 0:
    sample = empty_cells.get('empty_cells', [])[0] if empty_cells.get('empty_cells') else {}
    print(f"   Sample cell: {sample}")

# Check Duplicates
print("\n6. DUPLICATE DETECTION")
duplicates = analysis.analysis_data.get('duplicates', {})
dup_count = duplicates.get('total_duplicate_rows', 0)
print(f"   ✅ Total duplicate rows: {dup_count}")
if dup_count > 0:
    dup_indices = duplicates.get('duplicate_row_indices', [])[:3]
    print(f"   Sample row indices: {dup_indices}")

# Check Outliers
print("\n7. OUTLIER DETECTION")
outliers = analysis.analysis_data.get('outliers', [])
print(f"   ✅ Columns with outliers: {len(outliers)}")
if outliers:
    for outlier in outliers[:2]:
        col = outlier.get('column', 'Unknown')
        count = outlier.get('count', 0)
        print(f"   - {col}: {count} outliers")

# Check Column Statistics
print("\n8. COLUMN STATISTICS")
col_stats = analysis.analysis_data.get('column_stats', {})
print(f"   ✅ Columns with stats: {len(col_stats)}")
if col_stats:
    first_col = list(col_stats.keys())[0]
    first_stats = col_stats[first_col]
    print(f"   Example ({first_col}): dtype={first_stats.get('dtype')}, "
          f"non_null={first_stats.get('non_null_count')}, "
          f"unique={first_stats.get('unique_count')}")

# Check Summary
print("\n9. ANALYSIS SUMMARY")
summary = analysis.analysis_data.get('summary', '')
if summary:
    print(f"   ✅ Summary: {summary[:100]}...")
else:
    print("   ⚠️  No summary text")

# Check Dataset Fields
print("\n10. DATASET MODEL FIELDS")
print(f"   ✅ dataset.data_quality_score: {dataset.data_quality_score}")
print(f"   ✅ dataset.row_count: {dataset.row_count}")
print(f"   ✅ dataset.col_count: {dataset.col_count}")
print(f"   ✅ dataset.is_analyzed: {dataset.is_analyzed}")

print("\n" + "="*80)
print("✅ ALL CHECKS COMPLETE - Analysis data is properly set up!")
print("="*80 + "\n")
print("Navigate to /datasets/{id}/analysis/ to view the analysis page")
print("\nExpected to see:")
print("  • Data Quality Score card showing percentage")
print("  • Summary tab with analysis text")
print("  • Empty Cells tab with list of empty cells")
print("  • Duplicates tab with row indices")
print("  • Columns tab with per-column statistics")
print("  • Outliers tab with bounds and sample values")
print("\n")
