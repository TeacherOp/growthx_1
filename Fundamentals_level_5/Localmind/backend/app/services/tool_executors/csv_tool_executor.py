"""
CSV Tool Executor - Handles CSV analysis operations.

Educational Note: This executor provides comprehensive CSV analysis
capabilities including data profiling, statistics, filtering, and
quality assessment. Used by both the simple csv_service (for processing)
and the csv_analyzer_agent (for detailed analysis).

Key Design: CSV files are NOT chunked or embedded - we analyze them
on-demand using this executor. The executor reads the file from the
raw folder using project_id and source_id.
"""

import csv
import io
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime
import statistics

from app.utils.path_utils import get_raw_dir


class CSVToolExecutor:
    """
    Executor for CSV analysis operations.

    Educational Note: Provides intelligent data type detection,
    statistical analysis, and data quality assessment for CSV files.
    """

    # Common date formats for parsing
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ'
    ]

    def __init__(self):
        """Initialize the executor."""
        pass

    # =========================================================================
    # Main Entry Point
    # =========================================================================

    def execute_tool(
        self,
        tool_input: Dict[str, Any],
        project_id: str,
        source_id: str
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Execute CSV analysis tool.

        Args:
            tool_input: Tool parameters from Claude (operation, column, etc.)
            project_id: Project ID for file path
            source_id: Source ID (file is {source_id}.csv in raw folder)

        Returns:
            Tuple of (result_dict, is_termination)
        """
        operation = tool_input.get("operation", "summary")

        try:
            # Read CSV file from raw folder
            raw_dir = get_raw_dir(project_id)
            csv_path = raw_dir / f"{source_id}.csv"

            if not csv_path.exists():
                return {
                    "success": False,
                    "error": f"CSV file not found: {csv_path}"
                }, False

            with open(csv_path, "r", encoding="utf-8") as f:
                csv_content = f.read()

            # Parse CSV content
            data = self._parse_csv(csv_content)

            if not data:
                return {
                    "success": False,
                    "error": "CSV file is empty or could not be parsed"
                }, False

            columns = list(data[0].keys()) if data else []

            # Route to appropriate operation
            result = self._execute_operation(operation, data, columns, tool_input)
            return result, False

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze CSV: {str(e)}"
            }, False

    def _parse_csv(self, csv_content: str) -> List[Dict[str, str]]:
        """Parse CSV content into list of dictionaries."""
        try:
            # Try to detect dialect
            sample = csv_content[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            csv_reader = csv.DictReader(io.StringIO(csv_content), dialect=dialect)
            return list(csv_reader)
        except Exception as e:
            raise Exception(f"Failed to parse CSV: {str(e)}")

    def _execute_operation(
        self,
        operation: str,
        data: List[Dict],
        columns: List[str],
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route to the appropriate analysis operation."""

        if operation == "summary":
            return self._get_summary(data, columns)
        elif operation == "profile":
            return self._profile_data(data, columns)
        elif operation == "statistics":
            column = tool_input.get("column")
            return self._get_statistics(data, column)
        elif operation == "count_by_column":
            column = tool_input.get("column")
            return self._count_by_column(data, column)
        elif operation == "filter":
            column = tool_input.get("column")
            value = tool_input.get("value")
            operator = tool_input.get("operator", "equals")
            return self._filter_data(data, column, value, operator)
        elif operation == "search":
            term = tool_input.get("search_term")
            return self._search_data(data, term)
        elif operation == "group_by":
            column = tool_input.get("column")
            aggregation = tool_input.get("aggregation", "count")
            return self._group_by_column(data, column, aggregation)
        elif operation == "top_bottom":
            column = tool_input.get("column")
            n = tool_input.get("n", 10)
            return self._get_top_bottom(data, column, n)
        elif operation == "unique_values":
            columns_list = tool_input.get("columns", [])
            return self._get_unique_values(data, columns_list)
        elif operation == "data_quality":
            return self._check_data_quality(data, columns)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }

    # =========================================================================
    # Type Detection Helpers
    # =========================================================================

    def _detect_column_type(self, values: List[str]) -> str:
        """Detect the data type of a column based on its values."""
        if not values:
            return 'empty'

        # Sample values for type detection (max 100 for performance)
        sample = values[:min(100, len(values))]
        sample = [v for v in sample if v and str(v).strip()]

        if not sample:
            return 'empty'

        # Check for numeric types
        numeric_count = 0
        float_count = 0
        for val in sample:
            try:
                float(str(val).replace(',', ''))
                numeric_count += 1
                if '.' in str(val):
                    float_count += 1
            except ValueError:
                pass

        if numeric_count > len(sample) * 0.8:  # 80% threshold
            return 'float' if float_count > 0 else 'integer'

        # Check for dates
        date_count = 0
        for val in sample[:20]:
            if self._parse_date(str(val)):
                date_count += 1

        if date_count > len(sample[:20]) * 0.5:  # 50% threshold
            return 'date'

        # Check for boolean
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
        if all(str(v).lower() in bool_values for v in sample):
            return 'boolean'

        # Check for email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if sum(1 for v in sample if re.match(email_pattern, str(v))) > len(sample) * 0.5:
            return 'email'

        # Check for URL
        url_pattern = r'^https?://'
        if sum(1 for v in sample if re.match(url_pattern, str(v))) > len(sample) * 0.5:
            return 'url'

        return 'text'

    def _parse_date(self, value: str) -> Optional[datetime]:
        """Try to parse a string as a date."""
        if not value:
            return None

        for date_format in self.DATE_FORMATS:
            try:
                return datetime.strptime(value, date_format)
            except ValueError:
                continue
        return None

    def _to_numeric(self, value: str) -> Optional[float]:
        """Convert a value to numeric, handling common formats."""
        if not value:
            return None
        try:
            cleaned = str(value).replace(',', '').replace('$', '').replace('%', '').strip()
            return float(cleaned)
        except ValueError:
            return None

    # =========================================================================
    # Analysis Operations
    # =========================================================================

    def _get_summary(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Get enhanced summary with data type detection."""
        column_info = {}
        for col in columns:
            values = [row.get(col, '') for row in data]
            non_empty = [v for v in values if v and str(v).strip()]
            col_type = self._detect_column_type(values)

            column_info[col] = {
                "type": col_type,
                "non_empty": len(non_empty),
                "empty": len(values) - len(non_empty),
                "unique": len(set(non_empty))
            }

        return {
            "success": True,
            "operation": "summary",
            "total_rows": len(data),
            "total_columns": len(columns),
            "columns": columns,
            "column_info": column_info,
            "sample_data": data[:3],
            "recommendations": self._get_analysis_recommendations(column_info)
        }

    def _get_analysis_recommendations(self, column_info: Dict[str, Dict]) -> List[str]:
        """Suggest appropriate analyses based on data types."""
        recommendations = []

        numeric_cols = [col for col, info in column_info.items() if info["type"] in ['integer', 'float']]
        date_cols = [col for col, info in column_info.items() if info["type"] == 'date']
        text_cols = [col for col, info in column_info.items() if info["type"] == 'text']

        if numeric_cols:
            recommendations.append(f"Statistical analysis available for: {', '.join(numeric_cols[:3])}")
            if len(numeric_cols) > 1:
                recommendations.append("Correlation analysis possible between numeric columns")

        if date_cols:
            recommendations.append(f"Time series analysis available for: {', '.join(date_cols[:2])}")

        if text_cols:
            recommendations.append(f"Category analysis available for: {', '.join(text_cols[:3])}")

        return recommendations

    def _profile_data(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Comprehensive data profiling with statistics for each column."""
        profile = {}

        for col in columns:
            values = [row.get(col, '') for row in data]
            non_empty = [v for v in values if v and str(v).strip()]

            col_type = self._detect_column_type(values)
            profile[col] = {
                "type": col_type,
                "total_values": len(values),
                "non_empty_values": len(non_empty),
                "empty_values": len(values) - len(non_empty),
                "completeness": f"{(len(non_empty) / len(values) * 100):.1f}%",
                "unique_values": len(set(non_empty))
            }

            if col_type in ['integer', 'float']:
                numeric_values = [self._to_numeric(v) for v in non_empty]
                numeric_values = [v for v in numeric_values if v is not None]
                if numeric_values:
                    profile[col].update({
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "mean": round(statistics.mean(numeric_values), 2),
                        "median": round(statistics.median(numeric_values), 2),
                        "std_dev": round(statistics.stdev(numeric_values), 2) if len(numeric_values) > 1 else 0
                    })
            elif col_type == 'text':
                lengths = [len(str(v)) for v in non_empty]
                if lengths:
                    most_common = Counter(non_empty).most_common(3)
                    profile[col].update({
                        "min_length": min(lengths),
                        "max_length": max(lengths),
                        "avg_length": round(sum(lengths) / len(lengths), 1),
                        "most_common": [(val, count) for val, count in most_common]
                    })
            elif col_type == 'date':
                dates = [self._parse_date(str(v)) for v in non_empty]
                dates = [d for d in dates if d]
                if dates:
                    profile[col].update({
                        "earliest": min(dates).isoformat(),
                        "latest": max(dates).isoformat(),
                        "date_range_days": (max(dates) - min(dates)).days
                    })

        return {
            "success": True,
            "operation": "profile",
            "row_count": len(data),
            "column_count": len(columns),
            "column_profiles": profile,
            "data_quality_score": self._calculate_quality_score(profile)
        }

    def _calculate_quality_score(self, profile: Dict) -> float:
        """Calculate overall data quality score."""
        if not profile:
            return 0.0

        scores = []
        for col_profile in profile.values():
            completeness = float(col_profile['completeness'].rstrip('%')) / 100
            uniqueness = col_profile['unique_values'] / col_profile['non_empty_values'] if col_profile['non_empty_values'] > 0 else 0
            scores.append((completeness * 0.7) + (min(uniqueness, 1.0) * 0.3))

        return round(sum(scores) / len(scores) * 100, 1)

    def _get_statistics(self, data: List[Dict], column: str) -> Dict[str, Any]:
        """Get detailed statistics for a numeric column."""
        if not column:
            available = list(data[0].keys()) if data else []
            return {
                "success": False,
                "error": f"Column name required. Available columns: {available}"
            }

        if column not in data[0].keys():
            return {
                "success": False,
                "error": f"Column '{column}' not found. Available: {list(data[0].keys())}"
            }

        values = [row.get(column, '') for row in data]
        col_type = self._detect_column_type(values)

        if col_type not in ['integer', 'float']:
            return {
                "success": False,
                "error": f"Column '{column}' is not numeric (type: {col_type})"
            }

        numeric_values = [self._to_numeric(v) for v in values if v]
        numeric_values = [v for v in numeric_values if v is not None]

        if not numeric_values:
            return {
                "success": False,
                "error": f"No valid numeric values in column '{column}'"
            }

        sorted_values = sorted(numeric_values)
        n = len(sorted_values)

        def percentile(p):
            k = (n - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < n:
                return sorted_values[f] + c * (sorted_values[f + 1] - sorted_values[f])
            return sorted_values[f]

        return {
            "success": True,
            "operation": "statistics",
            "column": column,
            "count": len(numeric_values),
            "missing_values": len(values) - len(numeric_values),
            "statistics": {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "mean": round(statistics.mean(numeric_values), 2),
                "median": round(statistics.median(numeric_values), 2),
                "std_dev": round(statistics.stdev(numeric_values), 2) if n > 1 else 0,
                "variance": round(statistics.variance(numeric_values), 2) if n > 1 else 0,
                "percentiles": {
                    "25th": round(percentile(25), 2),
                    "50th": round(percentile(50), 2),
                    "75th": round(percentile(75), 2),
                    "90th": round(percentile(90), 2),
                    "95th": round(percentile(95), 2)
                },
                "iqr": round(percentile(75) - percentile(25), 2),
                "outliers": self._detect_outliers(numeric_values)
            }
        }

    def _detect_outliers(self, values: List[float]) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        if len(values) < 4:
            return {"count": 0, "values": []}

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [v for v in values if v < lower_bound or v > upper_bound]

        return {
            "count": len(outliers),
            "percentage": f"{(len(outliers) / len(values) * 100):.1f}%",
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "values": outliers[:10]
        }

    def _count_by_column(self, data: List[Dict], column: str) -> Dict[str, Any]:
        """Count unique values in a specific column."""
        if not column:
            available = list(data[0].keys()) if data else []
            return {
                "success": False,
                "error": f"Column name required. Available columns: {available}"
            }

        if column not in data[0].keys():
            return {
                "success": False,
                "error": f"Column '{column}' not found. Available: {list(data[0].keys())}"
            }

        counter = Counter(row[column] for row in data)

        return {
            "success": True,
            "operation": "count_by_column",
            "column": column,
            "unique_values": len(counter),
            "value_counts": dict(counter.most_common()),
            "top_10": dict(counter.most_common(10))
        }

    def _filter_data(
        self,
        data: List[Dict],
        column: str,
        value: str,
        operator: str = "equals"
    ) -> Dict[str, Any]:
        """Filter data by column value."""
        if not column:
            available = list(data[0].keys()) if data else []
            return {
                "success": False,
                "error": f"Column name required. Available columns: {available}"
            }

        if column not in data[0].keys():
            return {
                "success": False,
                "error": f"Column '{column}' not found. Available: {list(data[0].keys())}"
            }

        filtered_data = []

        for row in data:
            cell_value = row.get(column, '')

            if operator == "equals":
                if str(cell_value).lower() == str(value).lower():
                    filtered_data.append(row)
            elif operator == "not_equals":
                if str(cell_value).lower() != str(value).lower():
                    filtered_data.append(row)
            elif operator == "contains":
                if str(value).lower() in str(cell_value).lower():
                    filtered_data.append(row)
            elif operator == "not_contains":
                if str(value).lower() not in str(cell_value).lower():
                    filtered_data.append(row)
            elif operator in ["greater_than", "less_than", "greater_equal", "less_equal"]:
                num_val = self._to_numeric(cell_value)
                compare_val = self._to_numeric(value)
                if num_val is not None and compare_val is not None:
                    if operator == "greater_than" and num_val > compare_val:
                        filtered_data.append(row)
                    elif operator == "less_than" and num_val < compare_val:
                        filtered_data.append(row)
                    elif operator == "greater_equal" and num_val >= compare_val:
                        filtered_data.append(row)
                    elif operator == "less_equal" and num_val <= compare_val:
                        filtered_data.append(row)

        return {
            "success": True,
            "operation": "filter",
            "filter_column": column,
            "filter_value": value,
            "filter_operator": operator,
            "original_rows": len(data),
            "filtered_rows": len(filtered_data),
            "filtered_data": filtered_data[:20]
        }

    def _search_data(self, data: List[Dict], term: str) -> Dict[str, Any]:
        """Search for a term across all columns."""
        if not term:
            return {
                "success": False,
                "error": "Search term is required"
            }

        matches = []
        term_lower = term.lower()

        for row_index, row in enumerate(data):
            for column, value in row.items():
                if term_lower in str(value).lower():
                    matches.append({
                        "row_index": row_index,
                        "column": column,
                        "value": value,
                        "full_row": row
                    })
                    break

        return {
            "success": True,
            "operation": "search",
            "search_term": term,
            "total_matches": len(matches),
            "matches": matches[:20]
        }

    def _group_by_column(
        self,
        data: List[Dict],
        column: str,
        aggregation: str = "count"
    ) -> Dict[str, Any]:
        """Group data by column values with aggregation."""
        if not column:
            available = list(data[0].keys()) if data else []
            return {
                "success": False,
                "error": f"Column name required. Available columns: {available}"
            }

        if column not in data[0].keys():
            return {
                "success": False,
                "error": f"Column '{column}' not found. Available: {list(data[0].keys())}"
            }

        groups = {}
        for row in data:
            key = row[column]
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        group_summary = {}
        for key, rows in groups.items():
            group_summary[key] = {
                "count": len(rows),
                "sample_rows": rows[:3]
            }

        return {
            "success": True,
            "operation": "group_by",
            "group_column": column,
            "aggregation": aggregation,
            "total_groups": len(groups),
            "group_summary": group_summary
        }

    def _get_top_bottom(self, data: List[Dict], column: str, n: int) -> Dict[str, Any]:
        """Get top and bottom N values from a column."""
        if not column:
            available = list(data[0].keys()) if data else []
            return {
                "success": False,
                "error": f"Column name required. Available columns: {available}"
            }

        if column not in data[0].keys():
            return {
                "success": False,
                "error": f"Column '{column}' not found. Available: {list(data[0].keys())}"
            }

        values = []
        col_type = self._detect_column_type([row.get(column, '') for row in data])

        for row in data:
            val = row.get(column, '')
            if val:
                if col_type in ['integer', 'float']:
                    num_val = self._to_numeric(val)
                    if num_val is not None:
                        values.append((num_val, row))
                else:
                    values.append((val, row))

        if not values:
            return {
                "success": False,
                "error": f"No valid values in column '{column}'"
            }

        sorted_values = sorted(values, key=lambda x: x[0], reverse=(col_type in ['integer', 'float']))

        return {
            "success": True,
            "operation": "top_bottom",
            "column": column,
            "column_type": col_type,
            "total_values": len(values),
            "top_n": [{"value": v[0], "row": v[1]} for v in sorted_values[:n]],
            "bottom_n": [{"value": v[0], "row": v[1]} for v in sorted_values[-n:]] if len(sorted_values) > n else []
        }

    def _get_unique_values(self, data: List[Dict], columns_list: List[str]) -> Dict[str, Any]:
        """Get unique values for specified columns."""
        if not columns_list:
            columns_list = list(data[0].keys()) if data else []

        result = {}
        for col in columns_list:
            if col in data[0].keys():
                values = [row.get(col, '') for row in data]
                unique = list(set(v for v in values if v))
                result[col] = {
                    "count": len(unique),
                    "values": unique[:100],
                    "sample": unique[:10]
                }

        return {
            "success": True,
            "operation": "unique_values",
            "unique_values": result
        }

    def _check_data_quality(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Check for data quality issues."""
        issues = []

        # Check for empty columns
        for col in columns:
            values = [row.get(col, '') for row in data]
            non_empty = [v for v in values if v and str(v).strip()]
            if len(non_empty) == 0:
                issues.append(f"Column '{col}' is completely empty")
            elif len(non_empty) < len(values) * 0.1:
                issues.append(f"Column '{col}' is {100 - (len(non_empty)/len(values)*100):.1f}% empty")

        # Check for duplicate rows
        row_tuples = [tuple(row.values()) for row in data]
        unique_rows = len(set(row_tuples))
        if unique_rows < len(data):
            duplicate_count = len(data) - unique_rows
            issues.append(f"Found {duplicate_count} duplicate rows ({(duplicate_count/len(data)*100):.1f}%)")

        # Check for inconsistent data types
        for col in columns:
            values = [row.get(col, '') for row in data if row.get(col)]
            if len(values) > 10:
                types = set()
                for v in values[:50]:
                    if self._to_numeric(v) is not None:
                        types.add('numeric')
                    elif self._parse_date(str(v)):
                        types.add('date')
                    else:
                        types.add('text')
                if len(types) > 1:
                    issues.append(f"Column '{col}' has mixed data types: {', '.join(types)}")

        # Calculate quality score
        quality_score = 100
        quality_score -= len(issues) * 5
        quality_score = max(0, quality_score)

        return {
            "success": True,
            "operation": "data_quality",
            "row_count": len(data),
            "column_count": len(columns),
            "quality_score": quality_score,
            "issues_found": len(issues),
            "issues": issues,
            "recommendations": self._get_quality_recommendations(issues)
        }

    def _get_quality_recommendations(self, issues: List[str]) -> List[str]:
        """Get recommendations based on data quality issues."""
        recommendations = []

        if any("empty" in issue.lower() for issue in issues):
            recommendations.append("Consider removing or imputing values for empty columns")

        if any("duplicate" in issue.lower() for issue in issues):
            recommendations.append("Review and remove duplicate rows to ensure data integrity")

        if any("mixed data types" in issue.lower() for issue in issues):
            recommendations.append("Standardize data types within columns for consistent analysis")

        if not issues:
            recommendations.append("Data quality looks good! Ready for analysis")

        return recommendations


# Singleton instance
csv_tool_executor = CSVToolExecutor()
