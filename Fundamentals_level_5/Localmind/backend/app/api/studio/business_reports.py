"""
Business Report endpoints - AI-generated data-driven business reports.

Educational Note: Business reports demonstrate multi-agent orchestration:
1. business_report_agent_executor orchestrates the generation
2. The agent calls csv_analyzer_agent for data analysis and charts
3. Context from non-CSV sources is incorporated
4. Complete package: Markdown report + data visualizations

Agent Pattern:
- Uses business_report_agent_executor for orchestration
- Agent has tools for planning, data analysis, context search, and writing
- Calls csv_analyzer_agent internally for pandas/matplotlib operations
- Multi-step process with intermediate results
- Final output is a comprehensive markdown business report

Output Structure:
- Markdown file with frontmatter (title, report_type, etc.)
- Charts are stored in ai_outputs/images/ (via csv_analyzer_agent)
- Report markdown references charts by URL
- ZIP download available for full package

Routes:
- POST /projects/<id>/studio/business-report               - Start generation
- GET  /projects/<id>/studio/business-report-jobs/<id>     - Job status
- GET  /projects/<id>/studio/business-report-jobs          - List jobs
- GET  /projects/<id>/studio/business-reports/<file>       - Serve file
- GET  /projects/<id>/studio/business-reports/<id>/preview - Preview markdown
- GET  /projects/<id>/studio/business-reports/<id>/download - Download ZIP
- DELETE /projects/<id>/studio/business-report-jobs/<id>   - Delete job
"""
import io
import zipfile
from pathlib import Path
from flask import jsonify, request, current_app, send_file, Response
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.tool_executors.business_report_agent_executor import business_report_agent_executor
from app.utils.path_utils import get_studio_dir, get_ai_images_dir


@studio_bp.route('/projects/<project_id>/studio/business-report', methods=['POST'])
def generate_business_report(project_id: str):
    """
    Start business report generation via business report agent.

    Request Body:
        - source_id: UUID of the primary source (required)
        - direction: User's direction/guidance (optional)
        - report_type: Type of report (optional, default: executive_summary)
        - csv_source_ids: List of CSV source IDs to analyze (optional)
        - context_source_ids: List of non-CSV source IDs for context (optional)
        - focus_areas: List of focus areas/topics (optional)

    Response:
        - 202 Accepted with job_id for polling
    """
    try:
        data = request.get_json()

        # Validate input
        source_id = data.get('source_id')
        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400

        direction = data.get('direction', '')
        report_type = data.get('report_type', 'executive_summary')
        csv_source_ids = data.get('csv_source_ids', [])
        context_source_ids = data.get('context_source_ids', [])
        focus_areas = data.get('focus_areas', [])

        # Validate report_type
        valid_report_types = [
            'executive_summary', 'financial_report', 'performance_analysis',
            'market_research', 'operations_report', 'sales_report',
            'quarterly_review', 'annual_report'
        ]
        if report_type not in valid_report_types:
            report_type = 'executive_summary'

        # Execute via business_report_agent_executor (creates job and launches agent)
        result = business_report_agent_executor.execute(
            project_id=project_id,
            source_id=source_id,
            direction=direction,
            report_type=report_type,
            csv_source_ids=csv_source_ids,
            context_source_ids=context_source_ids,
            focus_areas=focus_areas
        )

        if not result.get('success'):
            return jsonify(result), 400

        return jsonify({
            'success': True,
            'job_id': result['job_id'],
            'status': result['status'],
            'message': result['message']
        }), 202

    except Exception as e:
        current_app.logger.error(f"Error starting business report generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start business report generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/business-report-jobs/<job_id>', methods=['GET'])
def get_business_report_job_status(project_id: str, job_id: str):
    """
    Get the status of a business report generation job.

    Response:
        - Job object with status, progress, and generated content
    """
    try:
        job = studio_index_service.get_business_report_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Business report job {job_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'job': job
        })

    except Exception as e:
        current_app.logger.error(f"Error getting business report job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/business-report-jobs', methods=['GET'])
def list_business_report_jobs(project_id: str):
    """
    List all business report jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - List of business report jobs (newest first)
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_business_report_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs
        })

    except Exception as e:
        current_app.logger.error(f"Error listing business report jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/business-reports/<filename>', methods=['GET'])
def get_business_report_file(project_id: str, filename: str):
    """
    Serve a business report file (markdown).

    Response:
        - Markdown file with appropriate headers
    """
    try:
        reports_dir = get_studio_dir(project_id) / "business_reports"
        filepath = reports_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'File not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(reports_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        # Determine mimetype
        if filename.endswith('.md'):
            mimetype = 'text/markdown'
        else:
            mimetype = 'application/octet-stream'

        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error serving business report file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve file: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/business-reports/<job_id>/preview', methods=['GET'])
def preview_business_report(project_id: str, job_id: str):
    """
    Serve business report markdown for preview.

    Response:
        - Markdown file content
    """
    try:
        # Get job to find markdown file
        job = studio_index_service.get_business_report_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Business report job {job_id} not found'
            }), 404

        markdown_file = job.get('markdown_file')
        if not markdown_file:
            return jsonify({
                'success': False,
                'error': 'Business report not yet generated'
            }), 404

        reports_dir = get_studio_dir(project_id) / "business_reports"
        filepath = reports_dir / markdown_file

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'Markdown file not found: {markdown_file}'
            }), 404

        # Read and return markdown content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return Response(
            content,
            mimetype='text/markdown',
            headers={'Content-Type': 'text/markdown; charset=utf-8'}
        )

    except Exception as e:
        current_app.logger.error(f"Error previewing business report: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview business report: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/business-reports/<job_id>/download', methods=['GET'])
def download_business_report(project_id: str, job_id: str):
    """
    Download business report as ZIP file (markdown + charts).

    Response:
        - ZIP file containing markdown and all associated charts
    """
    try:
        # Get job to find files
        job = studio_index_service.get_business_report_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Business report job {job_id} not found'
            }), 404

        markdown_file = job.get('markdown_file')
        if not markdown_file:
            return jsonify({
                'success': False,
                'error': 'Business report not yet generated'
            }), 404

        reports_dir = get_studio_dir(project_id) / "business_reports"
        images_dir = get_ai_images_dir(project_id)

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add markdown file
            markdown_path = reports_dir / markdown_file
            if markdown_path.exists():
                zip_file.write(markdown_path, markdown_file)

            # Add chart files from ai_outputs/images/
            charts = job.get('charts', [])
            for chart_info in charts:
                chart_filename = chart_info.get('filename')
                if chart_filename:
                    chart_path = images_dir / chart_filename
                    if chart_path.exists():
                        zip_file.write(chart_path, f"charts/{chart_filename}")

        zip_buffer.seek(0)

        # Generate filename from title
        title = job.get('title', 'business_report')
        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip()[:50]
        zip_filename = f"{safe_name}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading business report: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to download business report: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/business-report-jobs/<job_id>', methods=['DELETE'])
def delete_business_report_job(project_id: str, job_id: str):
    """
    Delete a business report job and its files.

    Note: Charts in ai_outputs/images/ are NOT deleted as they may be shared
    with other features or analysis sessions.

    Response:
        - Success status
    """
    try:
        # Get job to find files
        job = studio_index_service.get_business_report_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Business report job {job_id} not found'
            }), 404

        # Delete markdown file only (charts are shared)
        reports_dir = get_studio_dir(project_id) / "business_reports"

        markdown_file = job.get('markdown_file')
        if markdown_file:
            markdown_path = reports_dir / markdown_file
            if markdown_path.exists():
                markdown_path.unlink()

        # Delete job from index
        studio_index_service.delete_business_report_job(project_id, job_id)

        return jsonify({
            'success': True,
            'message': f'Business report job {job_id} deleted'
        })

    except Exception as e:
        current_app.logger.error(f"Error deleting business report job: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete business report job: {str(e)}'
        }), 500
