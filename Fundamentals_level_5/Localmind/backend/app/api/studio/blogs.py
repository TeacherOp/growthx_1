"""
Blog Post endpoints - AI-generated comprehensive blog posts.

Educational Note: Blog posts demonstrate agent-based generation with image support:
1. blog_agent_executor orchestrates the generation
2. Claude creates markdown structure and content
3. Gemini generates images for hero and sections
4. Complete package: Markdown + images

Agent Pattern:
- Uses blog_agent_executor for orchestration
- Agent has tools for planning, image generation, and writing
- Multi-step process with intermediate results
- Final output is a complete markdown blog post

Output Structure:
- Markdown file with frontmatter (title, meta_description, etc.)
- Image files for hero and section illustrations
- All files stored in project's studio/blogs folder
- ZIP download available for full package

Routes:
- POST /projects/<id>/studio/blog                        - Start generation
- GET  /projects/<id>/studio/blog-jobs/<id>              - Job status
- GET  /projects/<id>/studio/blog-jobs                   - List jobs
- GET  /projects/<id>/studio/blogs/<file>                - Serve file
- GET  /projects/<id>/studio/blogs/<id>/preview          - Preview markdown
- GET  /projects/<id>/studio/blogs/<id>/download         - Download ZIP
- DELETE /projects/<id>/studio/blog-jobs/<id>            - Delete job
"""
import io
import zipfile
from pathlib import Path
from flask import jsonify, request, current_app, send_file, Response
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.tool_executors.blog_agent_executor import blog_agent_executor
from app.utils.path_utils import get_studio_dir


@studio_bp.route('/projects/<project_id>/studio/blog', methods=['POST'])
def generate_blog_post(project_id: str):
    """
    Start blog post generation via blog agent.

    Request Body:
        - source_id: UUID of the source to generate blog from (required)
        - direction: User's direction/guidance (optional)
        - target_keyword: SEO keyword/phrase to target (optional)
        - blog_type: Category of blog post (optional, default: how_to_guide)

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
        target_keyword = data.get('target_keyword', '')
        blog_type = data.get('blog_type', 'how_to_guide')

        # Validate blog_type
        valid_blog_types = [
            'case_study', 'listicle', 'how_to_guide', 'opinion',
            'product_review', 'news', 'tutorial', 'comparison',
            'interview', 'roundup'
        ]
        if blog_type not in valid_blog_types:
            blog_type = 'how_to_guide'

        # Execute via blog_agent_executor (creates job and launches agent)
        result = blog_agent_executor.execute(
            project_id=project_id,
            source_id=source_id,
            direction=direction,
            target_keyword=target_keyword,
            blog_type=blog_type
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
        current_app.logger.error(f"Error starting blog post generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start blog post generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/blog-jobs/<job_id>', methods=['GET'])
def get_blog_job_status(project_id: str, job_id: str):
    """
    Get the status of a blog post generation job.

    Response:
        - Job object with status, progress, and generated content
    """
    try:
        job = studio_index_service.get_blog_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Blog job {job_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'job': job
        })

    except Exception as e:
        current_app.logger.error(f"Error getting blog job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/blog-jobs', methods=['GET'])
def list_blog_jobs(project_id: str):
    """
    List all blog post jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - List of blog jobs (newest first)
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_blog_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs
        })

    except Exception as e:
        current_app.logger.error(f"Error listing blog jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/blogs/<filename>', methods=['GET'])
def get_blog_file(project_id: str, filename: str):
    """
    Serve a blog file (markdown or image).

    Response:
        - Markdown file or image file with appropriate headers
    """
    try:
        blog_dir = get_studio_dir(project_id) / "blogs"
        filepath = blog_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'File not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(blog_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        # Determine mimetype
        if filename.endswith('.md'):
            mimetype = 'text/markdown'
        elif filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mimetype = 'image/jpeg'
        else:
            mimetype = 'application/octet-stream'

        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error serving blog file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve file: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/blogs/<job_id>/preview', methods=['GET'])
def preview_blog_post(project_id: str, job_id: str):
    """
    Serve blog post markdown for preview.

    Response:
        - Markdown file content
    """
    try:
        # Get job to find markdown file
        job = studio_index_service.get_blog_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Blog job {job_id} not found'
            }), 404

        markdown_file = job.get('markdown_file')
        if not markdown_file:
            return jsonify({
                'success': False,
                'error': 'Blog post not yet generated'
            }), 404

        blog_dir = get_studio_dir(project_id) / "blogs"
        filepath = blog_dir / markdown_file

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
        current_app.logger.error(f"Error previewing blog post: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview blog post: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/blogs/<job_id>/download', methods=['GET'])
def download_blog_post(project_id: str, job_id: str):
    """
    Download blog post as ZIP file (markdown + images).

    Response:
        - ZIP file containing markdown and all images
    """
    try:
        # Get job to find files
        job = studio_index_service.get_blog_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Blog job {job_id} not found'
            }), 404

        markdown_file = job.get('markdown_file')
        if not markdown_file:
            return jsonify({
                'success': False,
                'error': 'Blog post not yet generated'
            }), 404

        blog_dir = get_studio_dir(project_id) / "blogs"

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add markdown file
            markdown_path = blog_dir / markdown_file
            if markdown_path.exists():
                zip_file.write(markdown_path, markdown_file)

            # Add image files
            images = job.get('images', [])
            for image_info in images:
                image_filename = image_info.get('filename')
                if image_filename:
                    image_path = blog_dir / image_filename
                    if image_path.exists():
                        zip_file.write(image_path, f"images/{image_filename}")

        zip_buffer.seek(0)

        # Generate filename from title
        title = job.get('title', 'blog_post')
        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip()[:50]
        zip_filename = f"{safe_name}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading blog post: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to download blog post: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/blog-jobs/<job_id>', methods=['DELETE'])
def delete_blog_job(project_id: str, job_id: str):
    """
    Delete a blog post job and its files.

    Response:
        - Success status
    """
    try:
        # Get job to find files
        job = studio_index_service.get_blog_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Blog job {job_id} not found'
            }), 404

        # Delete files
        blog_dir = get_studio_dir(project_id) / "blogs"

        # Delete markdown file
        markdown_file = job.get('markdown_file')
        if markdown_file:
            markdown_path = blog_dir / markdown_file
            if markdown_path.exists():
                markdown_path.unlink()

        # Delete image files
        images = job.get('images', [])
        for image_info in images:
            image_filename = image_info.get('filename')
            if image_filename:
                image_path = blog_dir / image_filename
                if image_path.exists():
                    image_path.unlink()

        # Delete job from index
        studio_index_service.delete_blog_job(project_id, job_id)

        return jsonify({
            'success': True,
            'message': f'Blog job {job_id} deleted'
        })

    except Exception as e:
        current_app.logger.error(f"Error deleting blog job: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete blog job: {str(e)}'
        }), 500
