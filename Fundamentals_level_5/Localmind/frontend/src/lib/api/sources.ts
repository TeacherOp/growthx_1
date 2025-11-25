/**
 * Sources API Service
 * Educational Note: Handles all source operations with the backend.
 * Sources are documents, images, audio, and data files uploaded to projects.
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api/v1';

/**
 * Source metadata returned from the API
 */
export interface Source {
  id: string;
  project_id: string;
  name: string;
  original_filename: string;
  description: string;
  category: 'document' | 'audio' | 'image' | 'data';
  mime_type: string;
  file_extension: string;
  file_size: number;
  stored_filename: string;
  status: 'uploaded' | 'processing' | 'ready' | 'error';
  processing_info: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/**
 * Summary statistics for sources
 */
export interface SourcesSummary {
  total_count: number;
  total_size: number;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
}

/**
 * Allowed file extensions grouped by category
 */
export interface AllowedTypes {
  allowed_extensions: Record<string, string>;
  by_category: Record<string, string[]>;
}

// Maximum number of sources allowed per project
export const MAX_SOURCES = 100;

class SourcesAPI {
  /**
   * List all sources for a project
   */
  async listSources(projectId: string): Promise<Source[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/sources`
      );
      return response.data.sources;
    } catch (error) {
      console.error('Error fetching sources:', error);
      throw error;
    }
  }

  /**
   * Upload a new source file
   * Educational Note: Uses FormData for multipart file upload
   */
  async uploadSource(
    projectId: string,
    file: File,
    name?: string,
    description?: string
  ): Promise<Source> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (name) formData.append('name', name);
      if (description) formData.append('description', description);

      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/sources`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data.source;
    } catch (error) {
      console.error('Error uploading source:', error);
      throw error;
    }
  }

  /**
   * Get a specific source's metadata
   */
  async getSource(projectId: string, sourceId: string): Promise<Source> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/sources/${sourceId}`
      );
      return response.data.source;
    } catch (error) {
      console.error('Error fetching source:', error);
      throw error;
    }
  }

  /**
   * Update a source's metadata
   */
  async updateSource(
    projectId: string,
    sourceId: string,
    data: { name?: string; description?: string }
  ): Promise<Source> {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/projects/${projectId}/sources/${sourceId}`,
        data
      );
      return response.data.source;
    } catch (error) {
      console.error('Error updating source:', error);
      throw error;
    }
  }

  /**
   * Delete a source
   */
  async deleteSource(projectId: string, sourceId: string): Promise<void> {
    try {
      await axios.delete(
        `${API_BASE_URL}/projects/${projectId}/sources/${sourceId}`
      );
    } catch (error) {
      console.error('Error deleting source:', error);
      throw error;
    }
  }

  /**
   * Get the download URL for a source
   */
  getDownloadUrl(projectId: string, sourceId: string): string {
    return `${API_BASE_URL}/projects/${projectId}/sources/${sourceId}/download`;
  }

  /**
   * Get sources summary (counts and sizes)
   */
  async getSourcesSummary(projectId: string): Promise<SourcesSummary> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/sources/summary`
      );
      return response.data.summary;
    } catch (error) {
      console.error('Error fetching sources summary:', error);
      throw error;
    }
  }

  /**
   * Get allowed file types for upload
   */
  async getAllowedTypes(): Promise<AllowedTypes> {
    try {
      const response = await axios.get(`${API_BASE_URL}/sources/allowed-types`);
      return {
        allowed_extensions: response.data.allowed_extensions,
        by_category: response.data.by_category,
      };
    } catch (error) {
      console.error('Error fetching allowed types:', error);
      throw error;
    }
  }
}

export const sourcesAPI = new SourcesAPI();

/**
 * Helper function to format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Helper function to get icon name based on category
 */
export function getCategoryIcon(category: string): string {
  switch (category) {
    case 'document':
      return 'FileText';
    case 'audio':
      return 'Music';
    case 'image':
      return 'Image';
    case 'data':
      return 'Table';
    default:
      return 'File';
  }
}
