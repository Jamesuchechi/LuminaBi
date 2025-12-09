"""
Management command to re-analyze a dataset
Save this as: datasets/management/commands/reanalyze_dataset.py
"""

import os
from django.core.management.base import BaseCommand
from datasets.models import Dataset, FileAnalysis, DatasetVersion
from datasets.services import FileParser, FileAnalyzer
import numpy as np 


class Command(BaseCommand):
    help = 'Re-analyze a dataset by ID'

    def add_arguments(self, parser):
        parser.add_argument(
            'dataset_id',
            type=int,
            help='ID of the dataset to re-analyze'
        )

    def handle(self, *args, **options):
        dataset_id = options['dataset_id']
        
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            self.stdout.write(f"Found dataset: {dataset.name}")
            
            # Check if file exists
            if not os.path.exists(dataset.file.path):
                self.stdout.write(self.style.ERROR(f"File not found: {dataset.file.path}"))
                return
            
            self.stdout.write(f"File path: {dataset.file.path}")
            self.stdout.write(f"File type: {dataset.file_type}")
            
            # Parse file
            self.stdout.write("Parsing file...")
            df = FileParser.parse_file(dataset.file.path, dataset.file_type)
            self.stdout.write(self.style.SUCCESS(f"File parsed successfully!"))
            self.stdout.write(f"Shape: {df.shape} (rows={len(df)}, cols={len(df.columns)})")
            self.stdout.write(f"Columns: {list(df.columns)}")
            
            # Show first few rows
            self.stdout.write("\nFirst 5 rows:")
            self.stdout.write(str(df.head()))
            
            # Check for missing values
            self.stdout.write("\nMissing values per column:")
            missing = df.isna().sum()
            for col, count in missing.items():
                if count > 0:
                    self.stdout.write(f"  {col}: {count}")
            
            # Run analysis
            self.stdout.write("\nRunning analysis...")
            analyzer = FileAnalyzer(df)
            analysis = analyzer.analyze()
            
            self.stdout.write(self.style.SUCCESS("Analysis completed!"))
            self.stdout.write(f"Analysis keys: {list(analysis.keys())}")
            
            # Convert pandas types to JSON serializable types
            def convert_pandas_types(obj):
                """Recursively convert pandas/numpy types to native Python types."""
                if isinstance(obj, dict):
                    return {k: convert_pandas_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_pandas_types(item) for item in obj]
                elif isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            

            # Convert analysis data
            analysis_serializable = convert_pandas_types(analysis)
         
            # Display analysis results
            basic_stats = analysis.get('basic_stats', {})
            self.stdout.write(f"\nBasic Stats:")
            self.stdout.write(f"  Rows: {basic_stats.get('rows')}")
            self.stdout.write(f"  Columns: {basic_stats.get('columns')}")
            
            empty_cells = analysis.get('empty_cells', {})
            self.stdout.write(f"\nEmpty Cells:")
            self.stdout.write(f"  Total: {empty_cells.get('total_empty_cells')}")
            self.stdout.write(f"  Empty rows: {empty_cells.get('total_empty_rows')}")
            self.stdout.write(f"  Empty columns: {empty_cells.get('total_empty_columns')}")
            
            duplicates = analysis.get('duplicates', {})
            self.stdout.write(f"\nDuplicates:")
            self.stdout.write(f"  Total duplicate rows: {duplicates.get('total_duplicate_rows')}")
            
            outliers = analysis.get('outliers', [])
            self.stdout.write(f"\nOutliers:")
            self.stdout.write(f"  Columns with outliers: {len(outliers)}")
            for outlier in outliers:
                self.stdout.write(f"    {outlier.get('column')}: {outlier.get('count')} outliers")
            
            self.stdout.write(f"\nData Quality Score: {analysis.get('data_quality_score')}%")
            self.stdout.write(f"\nSummary: {analysis.get('summary')}")
            
            # Update dataset
            # Update dataset with converted data
            dataset.row_count = len(df)
            dataset.col_count = len(df.columns)
            dataset.column_names = list(df.columns)
            dataset.is_analyzed = True
            dataset.data_quality_score = analysis.get('data_quality_score', 0)
            dataset.summary = analysis.get('summary', '')
            dataset.empty_rows_count = empty_cells.get('total_empty_rows', 0)
            dataset.empty_cols_count = empty_cells.get('total_empty_columns', 0)
            dataset.empty_cells = convert_pandas_types(empty_cells.get('empty_cells', []))
            dataset.duplicate_rows = convert_pandas_types(duplicates.get('duplicate_row_indices', []))
            dataset.duplicate_values = convert_pandas_types(duplicates.get('duplicate_values_by_column', {}))
            dataset.analysis_metadata = analysis_serializable  # Use converted version
            dataset.save()
            
            self.stdout.write(self.style.SUCCESS(f"\nDataset {dataset.id} updated!"))
            
            file_analysis, created = FileAnalysis.objects.update_or_create(
            dataset=dataset,
            defaults={
                'analysis_data': analysis_serializable,  # Use converted version
                'empty_cells_detail': convert_pandas_types(empty_cells.get('empty_cells', [])),
                'column_stats': convert_pandas_types(analysis.get('column_stats', {})),
                'data_types': convert_pandas_types(analysis.get('data_types', {})),
                'missing_values': convert_pandas_types(analysis.get('missing_values', {})),
                'outliers': convert_pandas_types(outliers),
                }
            )
            
            self.stdout.write(self.style.SUCCESS(
                f"FileAnalysis {'created' if created else 'updated'}!"
            ))
            
            # Create version if doesn't exist
            if not dataset.versions.exists():
                version = DatasetVersion.objects.create(
                    dataset=dataset,
                    file=dataset.file,
                    version_number=1,
                    operation_type='upload',
                    operation_description=f'Initial upload: {dataset.file_type}',
                    metadata={'file_size': dataset.file_size, 'file_type': dataset.file_type},
                    rows_before=0,
                    rows_after=len(df),
                    is_current=True,
                )
                self.stdout.write(self.style.SUCCESS(f"DatasetVersion created!"))
            
            self.stdout.write(self.style.SUCCESS("\n✅ Re-analysis complete!"))
            self.stdout.write(f"Visit: http://localhost:8000/datasets/{dataset.id}/analysis/")
            
        except Dataset.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Dataset with ID {dataset_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())