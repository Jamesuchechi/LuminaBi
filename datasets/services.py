"""
File Analysis and Data Processing Services
Handles file parsing, analysis, cleaning, and visualization
"""

import os
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from io import StringIO, BytesIO

logger = logging.getLogger(__name__)


def convert_pandas_types(obj):
    """
    Recursively convert pandas/numpy types to native Python types for JSON serialization.
    
    Args:
        obj: Object potentially containing pandas/numpy types
        
    Returns:
        Object with all pandas/numpy types converted to native Python types
    """
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
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj

class FileParser:
    """Parse different file types"""

    SUPPORTED_FORMATS = {
        'csv': 'read_csv',
        'excel': 'read_excel',
        'json': 'read_json',
        'text': 'read_csv',
    }

    @staticmethod
    def parse_file(file_path: str, file_type: str) -> pd.DataFrame:
        """
        Parse file and return DataFrame
        
        Args:
            file_path: Path to file
            file_type: Type of file (csv, excel, json, text)
            
        Returns:
            pandas DataFrame
        """
        try:
            if file_type == 'csv' or file_type == 'text':
                # Handle various representations of missing data
                # Including 'N/A', 'NA', 'n/a', empty strings, etc.
                df = pd.read_csv(
                    file_path,
                    na_values=['N/A', 'n/a', 'NA', 'na', 'null', 'NULL', 'None', '', ' '],
                    keep_default_na=True
                )
            elif file_type == 'excel':
                df = pd.read_excel(
                    file_path,
                    na_values=['N/A', 'n/a', 'NA', 'na', 'null', 'NULL', 'None', '', ' '],
                    keep_default_na=True
                )
            elif file_type == 'json':
                df = pd.read_json(file_path)
                # Replace string 'N/A' with actual NaN in JSON
                df = df.replace(['N/A', 'n/a', 'NA', 'na', 'null', 'NULL', 'None'], np.nan)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            logger.info(f"Parsed {file_type} file: {df.shape[0]} rows, {df.shape[1]} columns")
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"Missing values per column:\n{df.isna().sum()}")
            
            return df
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            raise

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(file_path)

    @staticmethod
    def detect_file_type(file_name: str) -> str:
        """Detect file type from extension"""
        ext = Path(file_name).suffix.lower()
        type_map = {
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.json': 'json',
            '.txt': 'text',
            '.pdf': 'pdf',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
        }
        return type_map.get(ext, 'csv')


class FileAnalyzer:
    """Analyze file content and structure"""

    def __init__(self, df: pd.DataFrame):
        """Initialize with DataFrame"""
        self.df = df
        self.analysis = {}

    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete analysis
        
        Returns:
            Dictionary with all analysis results
        """
        self.analysis = {
            'basic_stats': self._analyze_basic_stats(),
            'empty_cells': self._analyze_empty_cells(),
            'duplicates': self._analyze_duplicates(),
            'column_stats': self._analyze_column_stats(),
            'data_types': self._analyze_data_types(),
            'missing_values': self._analyze_missing_values(),
            'outliers': self._detect_outliers(),
            'summary': self._generate_summary(),
            'data_quality_score': self._calculate_data_quality(),
        }
        return self.analysis

    def _analyze_basic_stats(self) -> Dict[str, Any]:
        """Analyze basic statistics"""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'column_names': list(self.df.columns),
            'size': self.df.memory_usage(deep=True).sum(),
            'shape': self.df.shape,
        }

    def _analyze_empty_cells(self) -> Dict[str, Any]:
        """Analyze empty/null cells"""
        empty_cells = []
        empty_rows = []
        empty_cols = []

        # Find empty cells with their coordinates
        for col_idx, col in enumerate(self.df.columns):
            for row_idx, value in enumerate(self.df[col]):
                if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                    # Convert to Excel-style coordinates (A1, B2, etc.)
                    cell_coord = f"{self._num_to_col(col_idx)}{row_idx + 2}"  # +2 because row 1 is header
                    empty_cells.append({
                        'cell': cell_coord,
                        'row': row_idx,
                        'column': col,
                        'col_index': col_idx,
                    })

        # Find completely empty rows
        for row_idx, row in self.df.iterrows():
            if row.isna().all():
                empty_rows.append(row_idx)

        # Find completely empty columns
        for col in self.df.columns:
            if self.df[col].isna().all() or (self.df[col] == '').all():
                empty_cols.append(col)

        return {
            'total_empty_cells': len(empty_cells),
            'empty_cells': empty_cells[:1000],  # Limit to first 1000 for performance
            'total_empty_rows': len(empty_rows),
            'empty_row_indices': empty_rows,
            'total_empty_columns': len(empty_cols),
            'empty_column_names': empty_cols,
        }

    def _analyze_duplicates(self) -> Dict[str, Any]:
        """Analyze duplicate rows and values"""
        duplicate_rows = self.df[self.df.duplicated(keep=False)].index.tolist()
        
        # Find duplicate values per column
        duplicate_values = {}
        for col in self.df.columns:
            duplicates = self.df[self.df.duplicated(subset=[col], keep=False)][col].value_counts()
            if len(duplicates) > 0:
                duplicate_values[col] = duplicates.to_dict()

        return {
            'total_duplicate_rows': len(self.df) - len(self.df.drop_duplicates()),
            'duplicate_row_indices': duplicate_rows[:1000],  # Limit for performance
            'duplicate_values_by_column': duplicate_values,
        }

    def _analyze_column_stats(self) -> Dict[str, Any]:
        """Analyze statistics for each column"""
        stats = {}
        for col in self.df.columns:
            col_data = self.df[col]
            stats[col] = {
                'non_null_count': col_data.notna().sum(),
                'null_count': col_data.isna().sum(),
                'unique_count': col_data.nunique(),
                'dtype': str(col_data.dtype),
            }
            
            # Add numeric stats if applicable
            if pd.api.types.is_numeric_dtype(col_data):
                stats[col].update({
                    'min': float(col_data.min()),
                    'max': float(col_data.max()),
                    'mean': float(col_data.mean()),
                    'median': float(col_data.median()),
                    'std': float(col_data.std()),
                })
        
        return stats

    def _analyze_data_types(self) -> Dict[str, str]:
        """Analyze data types of each column"""
        return {col: str(dtype) for col, dtype in self.df.dtypes.items()}

    def _analyze_missing_values(self) -> Dict[str, int]:
        """Analyze missing values per column"""
        return {col: int(self.df[col].isna().sum()) for col in self.df.columns}

    def _detect_outliers(self) -> List[Dict[str, Any]]:
        """Detect outliers using IQR method"""
        outliers = []
        
        for col in self.df.select_dtypes(include=[np.number]).columns:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_rows = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            
            if len(outlier_rows) > 0:
                outliers.append({
                    'column': col,
                    'count': len(outlier_rows),
                    'bounds': {'lower': float(lower_bound), 'upper': float(upper_bound)},
                    'sample_values': outlier_rows[col].head(5).tolist(),
                })
        
        return outliers[:100]  # Limit for performance

    def _generate_summary(self) -> str:
        """Generate rule-based summary"""
        rows = len(self.df)
        cols = len(self.df.columns)
        missing_pct = (self.df.isna().sum().sum() / (rows * cols)) * 100
        duplicate_pct = ((len(self.df) - len(self.df.drop_duplicates())) / len(self.df)) * 100

        quality = "Good"
        if missing_pct > 20 or duplicate_pct > 10:
            quality = "Needs Cleaning"
        elif missing_pct > 5 or duplicate_pct > 5:
            quality = "Fair"

        summary = f"Dataset with {rows} rows and {cols} columns. "
        summary += f"Missing values: {missing_pct:.1f}%. "
        summary += f"Duplicate rows: {duplicate_pct:.1f}%. "
        summary += f"Overall quality: {quality}."

        return summary

    def _calculate_data_quality(self) -> float:
        """Calculate data quality score (0-100)"""
        rows = len(self.df)
        cols = len(self.df.columns)
        
        # Missing values impact (30%)
        missing_pct = (self.df.isna().sum().sum() / (rows * cols)) * 100
        missing_score = max(0, 100 - (missing_pct * 3))  # 3% decrease per 1% missing
        
        # Duplicates impact (20%)
        duplicate_pct = ((len(self.df) - len(self.df.drop_duplicates())) / len(self.df)) * 100
        duplicate_score = max(0, 100 - (duplicate_pct * 2))
        
        # Outliers impact (10%)
        outlier_score = 100  # Base score
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = len(self.df[(self.df[col] < Q1 - 1.5*IQR) | (self.df[col] > Q3 + 1.5*IQR)])
            outlier_pct = (outlier_count / len(self.df)) * 100
            outlier_score -= min(10, outlier_pct)
        
        # Completeness impact (40%)
        null_cols = len(self.df.columns[self.df.isna().all()])
        completeness_score = max(0, 100 - (null_cols / cols * 100))

        # Weighted score
        total_score = (
            (missing_score * 0.30) +
            (duplicate_score * 0.20) +
            (outlier_score * 0.10) +
            (completeness_score * 0.40)
        )

        return round(total_score, 2)

    @staticmethod
    def _num_to_col(n: int) -> str:
        """Convert column number to letter (0=A, 1=B, etc.)"""
        result = ''
        while n >= 0:
            result = chr(65 + (n % 26)) + result
            n = n // 26 - 1
        return result


class DataCleaner:
    """Data cleaning operations"""

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: List[str] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Remove duplicate rows
        
        Args:
            df: Input DataFrame
            subset: Columns to consider for duplicates (None = all columns)
            
        Returns:
            Cleaned DataFrame and operation details
        """
        duplicates_removed = len(df) - len(df.drop_duplicates(subset=subset))
        df_cleaned = df.drop_duplicates(subset=subset, ignore_index=True)

        return df_cleaned, {
            'duplicates_removed': duplicates_removed,
            'rows_before': len(df),
            'rows_after': len(df_cleaned),
        }

    @staticmethod
    def fill_empty_cells(df: pd.DataFrame, fill_values: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict]:
        """
        Fill empty cells with specified values
        
        Args:
            df: Input DataFrame
            fill_values: Dict with column names and fill values
            
        Returns:
            Filled DataFrame and operation details
        """
        df_filled = df.copy()
        changes = {}

        for column, value in fill_values.items():
            if column in df_filled.columns:
                empty_count = df_filled[column].isna().sum()
                df_filled[column].fillna(value, inplace=True)
                changes[column] = {
                    'value': str(value),
                    'cells_filled': empty_count,
                }

        return df_filled, {
            'total_cells_filled': sum(v['cells_filled'] for v in changes.values()),
            'columns_modified': changes,
        }

    @staticmethod
    def fill_empty_cells_by_address(df: pd.DataFrame, cells_to_fill: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict]:
        """
        Fill specific cells by address (e.g., A4, B9)
        
        Args:
            df: Input DataFrame
            cells_to_fill: Dict like {'A4': 'value', 'B9': 100}
            
        Returns:
            Filled DataFrame and operation details
        """
        df_filled = df.copy()
        changes = []

        for cell_addr, value in cells_to_fill.items():
            try:
                # Parse cell address (A4 -> col 0, row 3)
                col_letter = ''.join([c for c in cell_addr if c.isalpha()])
                row_num = int(''.join([c for c in cell_addr if c.isdigit()]))
                
                col_idx = ord(col_letter.upper()) - ord('A')
                row_idx = row_num - 2  # -1 for 0-index, -1 for header
                
                if col_idx < len(df_filled.columns) and row_idx >= 0:
                    col_name = df_filled.columns[col_idx]
                    df_filled.iloc[row_idx, col_idx] = value
                    changes.append({
                        'cell': cell_addr,
                        'column': col_name,
                        'row': row_idx,
                        'value': str(value),
                    })
            except Exception as e:
                logger.warning(f"Could not fill cell {cell_addr}: {str(e)}")

        return df_filled, {
            'total_cells_filled': len(changes),
            'changes': changes,
        }

    @staticmethod
    def remove_whitespace(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Remove leading/trailing whitespace from all string columns"""
        df_cleaned = df.copy()
        columns_modified = 0

        for col in df_cleaned.select_dtypes(include=['object']).columns:
            original = df_cleaned[col].copy()
            df_cleaned[col] = df_cleaned[col].str.strip()
            if not original.equals(df_cleaned[col]):
                columns_modified += 1

        return df_cleaned, {
            'columns_modified': columns_modified,
            'operation': 'remove_whitespace',
        }

    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Normalize column names (lowercase, replace spaces with underscore)"""
        df_normalized = df.copy()
        old_names = df_normalized.columns.tolist()
        
        df_normalized.columns = [
            col.lower().replace(' ', '_').replace('-', '_').strip('_')
            for col in df_normalized.columns
        ]
        
        new_names = df_normalized.columns.tolist()
        renames = dict(zip(old_names, new_names))

        return df_normalized, {
            'columns_renamed': {k: v for k, v in renames.items() if k != v},
            'operation': 'normalize_column_names',
        }

    @staticmethod
    def convert_types(df: pd.DataFrame, type_mapping: Dict[str, str]) -> Tuple[pd.DataFrame, Dict]:
        """
        Convert column types
        
        Args:
            df: Input DataFrame
            type_mapping: Dict like {'age': 'int', 'price': 'float'}
        """
        df_converted = df.copy()
        conversions = {}

        type_map = {
            'int': 'int64',
            'float': 'float64',
            'str': 'object',
            'bool': 'bool',
        }

        for col, target_type in type_mapping.items():
            if col in df_converted.columns:
                try:
                    old_type = str(df_converted[col].dtype)
                    df_converted[col] = df_converted[col].astype(type_map.get(target_type, target_type))
                    conversions[col] = {
                        'from': old_type,
                        'to': target_type,
                    }
                except Exception as e:
                    logger.warning(f"Could not convert {col} to {target_type}: {str(e)}")

        return df_converted, {
            'conversions': conversions,
            'operation': 'convert_types',
        }

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = 'mean') -> Tuple[pd.DataFrame, Dict]:
        """
        Handle missing values
        
        Args:
            df: Input DataFrame
            strategy: 'mean', 'median', 'forward_fill', 'drop', or 'drop_column'
        """
        df_handled = df.copy()
        changes = {}

        if strategy == 'mean':
            numeric_cols = df_handled.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_handled[col].isna().sum() > 0:
                    before = df_handled[col].isna().sum()
                    df_handled[col].fillna(df_handled[col].mean(), inplace=True)
                    changes[col] = {'method': 'mean', 'filled': before}

        elif strategy == 'median':
            numeric_cols = df_handled.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_handled[col].isna().sum() > 0:
                    before = df_handled[col].isna().sum()
                    df_handled[col].fillna(df_handled[col].median(), inplace=True)
                    changes[col] = {'method': 'median', 'filled': before}

        elif strategy == 'forward_fill':
            for col in df_handled.columns:
                if df_handled[col].isna().sum() > 0:
                    before = df_handled[col].isna().sum()
                    df_handled[col].fillna(method='ffill', inplace=True)
                    df_handled[col].fillna(method='bfill', inplace=True)
                    changes[col] = {'method': 'forward_fill', 'filled': before}

        elif strategy == 'drop':
            before_rows = len(df_handled)
            df_handled = df_handled.dropna()
            changes['dropped_rows'] = before_rows - len(df_handled)

        elif strategy == 'drop_column':
            cols_before = len(df_handled.columns)
            df_handled = df_handled.dropna(axis=1)
            changes['dropped_columns'] = cols_before - len(df_handled.columns)

        return df_handled, {
            'strategy': strategy,
            'changes': changes,
            'operation': 'handle_missing_values',
        }


class FileExporter:
    """Export data to different formats"""

    @staticmethod
    def to_csv(df: pd.DataFrame, file_path: str) -> str:
        """Export to CSV"""
        df.to_csv(file_path, index=False)
        return file_path

    @staticmethod
    def to_excel(df: pd.DataFrame, file_path: str) -> str:
        """Export to Excel"""
        df.to_excel(file_path, index=False)
        return file_path

    @staticmethod
    def to_json(df: pd.DataFrame, file_path: str) -> str:
        """Export to JSON"""
        df.to_json(file_path, orient='records', indent=2)
        return file_path

    @staticmethod
    def to_dict(df: pd.DataFrame) -> Dict:
        """Convert to dictionary"""
        return df.to_dict(orient='records')

    @staticmethod
    def get_sample(df: pd.DataFrame, n_rows: int = 100) -> pd.DataFrame:
        """Get sample of data"""
        return df.head(n_rows)
