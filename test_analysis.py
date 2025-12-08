#!/usr/bin/env python3
"""
Test script to verify analysis data structure and functionality
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Luminabi.settings')
django.setup()

from datasets.models import Dataset, FileAnalysis
from datasets.services import FileAnalyzer, FileParser

# Check existing analyses
print("=" * 80)
print("CHECKING EXISTING ANALYSES")
print("=" * 80)

analyses = FileAnalysis.objects.all()[:3]

for analysis in analyses:
    print(f"\nDataset: {analysis.dataset.name}")
    print(f"  - Analysis Data Keys: {list(analysis.analysis_data.keys()) if analysis.analysis_data else 'None'}")
    
    if analysis.analysis_data:
        data = analysis.analysis_data
        
        # Basic Stats
        if 'basic_stats' in data:
            bs = data['basic_stats']
            print(f"  - Basic Stats: {bs.get('rows')} rows × {bs.get('columns')} cols")
        
        # Quality Score
        if 'data_quality_score' in data:
            print(f"  - Quality Score: {data['data_quality_score']:.1f}%")
        
        # Empty Cells
        if 'empty_cells' in data:
            ec = data['empty_cells']
            print(f"  - Empty Cells: {ec.get('total_empty_cells', 0)} total")
        
        # Duplicates
        if 'duplicates' in data:
            dup = data['duplicates']
            print(f"  - Duplicates: {dup.get('total_duplicate_rows', 0)} rows")
        
        # Outliers
        if 'outliers' in data:
            outliers = data['outliers']
            print(f"  - Outliers: {len(outliers)} columns with outliers")
            for outlier in outliers[:2]:
                if isinstance(outlier, dict):
                    print(f"    * {outlier.get('column')}: {outlier.get('count')} outliers")
        
        # Summary
        if 'summary' in data:
            summary = data['summary']
            print(f"  - Summary: {summary[:80]}...")

print("\n" + "=" * 80)
print("ANALYSIS CHECK COMPLETE")
print("=" * 80)
