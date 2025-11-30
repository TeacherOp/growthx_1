"""
Analysis Executor - Executes pandas/numpy/matplotlib code for data analysis.

Educational Note: This executor enables dynamic data analysis by:
1. Loading CSV data into a pandas DataFrame
2. Executing Python code written by the AI agent
3. Capturing results (data or plots)
4. Returning formatted output

The AI agent writes pandas code based on user questions,
making it flexible for any analysis task.
"""

import uuid
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np

from app.utils.path_utils import get_raw_dir, get_ai_images_dir


class AnalysisExecutor:
    """
    Executor for running pandas analysis code on CSV data.

    Educational Note: Instead of pre-defined operations, this executor
    lets the AI write custom pandas code for flexible analysis.
    """

    def __init__(self):
        """Initialize the executor."""
        self._df_cache: Dict[str, pd.DataFrame] = {}

    def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        project_id: str,
        source_id: str
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Execute analysis tool.

        Args:
            tool_name: Name of the tool (run_analysis or return_analysis)
            tool_input: Tool parameters
            project_id: Project ID for file paths
            source_id: Source ID of the CSV file

        Returns:
            Tuple of (result_dict, is_termination)
        """
        if tool_name == "run_analysis":
            return self._run_analysis(tool_input, project_id, source_id), False
        elif tool_name == "return_analysis":
            return tool_input, True
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}, False

    def _load_dataframe(self, project_id: str, source_id: str) -> pd.DataFrame:
        """
        Load CSV into DataFrame with caching.

        Educational Note: We cache the DataFrame to avoid re-reading
        the file on every query during an analysis session.
        """
        cache_key = f"{project_id}_{source_id}"

        if cache_key not in self._df_cache:
            raw_dir = get_raw_dir(project_id)
            csv_path = raw_dir / f"{source_id}.csv"

            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")

            self._df_cache[cache_key] = pd.read_csv(csv_path)

        return self._df_cache[cache_key].copy()

    def _run_analysis(
        self,
        tool_input: Dict[str, Any],
        project_id: str,
        source_id: str
    ) -> Dict[str, Any]:
        """
        Execute pandas code and return result.

        Educational Note: We create a safe execution environment with:
        - df: The loaded DataFrame
        - pd: pandas
        - np: numpy
        - plt: matplotlib.pyplot
        - sns: seaborn

        The AI assigns its output to 'result' variable.
        """
        code = tool_input.get("code", "")

        if not code:
            return {"success": False, "error": "No code provided"}

        # Import visualization libraries at top of method
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        import seaborn as sns

        # Store original savefig methods BEFORE try block
        original_plt_savefig = plt.savefig
        original_fig_savefig = Figure.savefig

        # Track saved plots
        saved_plots = []

        try:
            # Load the DataFrame
            df = self._load_dataframe(project_id, source_id)

            # Setup images directory
            images_dir = get_ai_images_dir(project_id)

            def custom_savefig(*args, **kwargs):
                """
                Intercept savefig to save plots to ai_outputs/images folder.

                Educational Note: We ALWAYS use auto-generated unique names to avoid
                conflicts and caching issues. Whatever filename Claude passes is ignored.
                """
                # Always use auto-generated unique name (full UUID for uniqueness)
                plot_id = str(uuid.uuid4())
                plot_filename = f"{source_id}_plot_{plot_id}.png"
                plot_path = images_dir / plot_filename

                kwargs.setdefault('dpi', 150)
                kwargs.setdefault('bbox_inches', 'tight')

                try:
                    # Determine if called as fig.savefig(filename) or plt.savefig(filename)
                    if args and isinstance(args[0], Figure):
                        # Called as fig.savefig() - first arg is figure instance
                        original_fig_savefig(args[0], plot_path, **kwargs)
                    else:
                        # Called as plt.savefig() - ignore any filename arg
                        original_plt_savefig(plot_path, **kwargs)

                    # Verify file actually exists before claiming success
                    if plot_path.exists() and plot_path.stat().st_size > 0:
                        saved_plots.append(plot_filename)
                        print(f"  Plot saved: {plot_filename}")
                    else:
                        print(f"  ERROR: Plot failed to save: {plot_filename}")

                except Exception as save_error:
                    print(f"  ERROR saving plot: {save_error}")

            # Patch both plt.savefig and Figure.savefig
            plt.savefig = custom_savefig
            Figure.savefig = custom_savefig

            # Create execution namespace
            exec_globals = {
                "df": df,
                "pd": pd,
                "np": np,
                "plt": plt,
                "sns": sns,
                "result": None
            }

            # Execute the code
            exec(code, exec_globals)

            # Get the result
            result = exec_globals.get("result")

            output = {"success": True}

            # Include saved plot filenames
            if saved_plots:
                output["plot_filenames"] = saved_plots
                output["output"] = f"Plot saved as: {saved_plots[-1]}"

            if result is not None:
                if "output" in output:
                    output["output"] += f"\n\nResult:\n{self._format_result(result)}"
                else:
                    output["output"] = self._format_result(result)

            if "output" not in output:
                output["output"] = "Code executed successfully (no output)"

            return output

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }

        finally:
            # ALWAYS restore original savefig methods and clean up
            plt.savefig = original_plt_savefig
            Figure.savefig = original_fig_savefig
            plt.close('all')

    def _format_result(self, result: Any) -> str:
        """
        Format pandas/numpy result as readable string.

        Educational Note: Different result types need different formatting:
        - DataFrame/Series: Use to_string() with limits
        - Scalar: Convert directly
        - Other: Use str()
        """
        if isinstance(result, pd.DataFrame):
            if len(result) > 50:
                return f"DataFrame with {len(result)} rows, {len(result.columns)} columns:\n\n{result.head(20).to_string()}\n\n... ({len(result) - 20} more rows)"
            return result.to_string()

        elif isinstance(result, pd.Series):
            if len(result) > 50:
                return f"Series with {len(result)} items:\n\n{result.head(20).to_string()}\n\n... ({len(result) - 20} more items)"
            return result.to_string()

        elif isinstance(result, (int, float, str, bool)):
            return str(result)

        elif isinstance(result, (list, dict)):
            import json
            return json.dumps(result, indent=2, default=str)

        elif isinstance(result, np.ndarray):
            if result.size > 100:
                return f"Array with shape {result.shape}:\n{result[:20]}...\n"
            return str(result)

        else:
            return str(result)

    def clear_cache(self, project_id: str = None, source_id: str = None):
        """Clear DataFrame cache."""
        if project_id and source_id:
            cache_key = f"{project_id}_{source_id}"
            self._df_cache.pop(cache_key, None)
        else:
            self._df_cache.clear()


# Singleton instance
analysis_executor = AnalysisExecutor()
