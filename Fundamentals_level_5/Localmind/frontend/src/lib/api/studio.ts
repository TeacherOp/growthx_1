/**
 * Studio API Service
 * Educational Note: Handles all studio generation operations with the backend.
 * Studio features generate content from sources (audio overviews, ad creatives, etc.)
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api/v1';

/**
 * Job status - shared across studio features
 */
export type JobStatus = 'pending' | 'processing' | 'ready' | 'error';

/**
 * Audio job status (alias for backwards compatibility)
 */
export type AudioJobStatus = JobStatus;

/**
 * Audio job record from the API
 */
export interface AudioJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: AudioJobStatus;
  progress: string;
  error: string | null;
  audio_path: string | null;
  audio_filename: string | null;
  audio_url: string | null;
  script_path: string | null;
  audio_info: {
    file_size_bytes?: number;
    estimated_duration_seconds?: number;
    word_count?: number;
    voice_id?: string;
    model_id?: string;
  } | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting audio generation
 */
export interface StartAudioResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  source_name?: string;
  error?: string;
}

/**
 * Response from getting job status
 */
export interface JobStatusResponse {
  success: boolean;
  job?: AudioJob;
  error?: string;
}

/**
 * Response from listing jobs
 */
export interface ListJobsResponse {
  success: boolean;
  jobs: AudioJob[];
  count: number;
  error?: string;
}

/**
 * TTS configuration status
 */
export interface TTSStatusResponse {
  success: boolean;
  configured: boolean;
  error?: string;
}

/**
 * Ad creative image info
 */
export interface AdImage {
  filename: string;
  path: string;
  url: string;
  type: string;
  prompt: string;
  index: number;
}

/**
 * Ad creative job record from the API
 */
export interface AdJob {
  id: string;
  product_name: string;
  direction: string;
  status: JobStatus;
  progress: string;
  error: string | null;
  images: AdImage[];
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting ad creative generation
 */
export interface StartAdResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  product_name?: string;
  error?: string;
}

/**
 * Response from getting ad job status
 */
export interface AdJobStatusResponse {
  success: boolean;
  job?: AdJob;
  error?: string;
}

/**
 * Response from listing ad jobs
 */
export interface ListAdJobsResponse {
  success: boolean;
  jobs: AdJob[];
  count: number;
  error?: string;
}

/**
 * Flash card item
 */
export interface FlashCard {
  front: string;
  back: string;
  category: 'definition' | 'concept' | 'application' | 'comparison';
}

/**
 * Flash card job record from the API
 */
export interface FlashCardJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  progress: string;
  error: string | null;
  cards: FlashCard[];
  topic_summary: string | null;
  card_count: number;
  generation_time_seconds: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting flash card generation
 */
export interface StartFlashCardsResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  source_name?: string;
  error?: string;
}

/**
 * Response from getting flash card job status
 */
export interface FlashCardJobStatusResponse {
  success: boolean;
  job?: FlashCardJob;
  error?: string;
}

/**
 * Response from listing flash card jobs
 */
export interface ListFlashCardJobsResponse {
  success: boolean;
  jobs: FlashCardJob[];
  count: number;
  error?: string;
}

/**
 * Mind map node from Claude
 */
export interface MindMapNode {
  id: string;
  label: string;
  parent_id: string | null;
  node_type: 'root' | 'category' | 'leaf';
  description: string;
}

/**
 * Mind map job record from the API
 */
export interface MindMapJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  progress: string;
  error: string | null;
  nodes: MindMapNode[];
  topic_summary: string | null;
  node_count: number;
  generation_time_seconds: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting mind map generation
 */
export interface StartMindMapResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  source_name?: string;
  error?: string;
}

/**
 * Response from getting mind map job status
 */
export interface MindMapJobStatusResponse {
  success: boolean;
  job?: MindMapJob;
  error?: string;
}

/**
 * Response from listing mind map jobs
 */
export interface ListMindMapJobsResponse {
  success: boolean;
  jobs: MindMapJob[];
  count: number;
  error?: string;
}

/**
 * Quiz option (answer choice)
 */
export interface QuizOption {
  id: string;
  text: string;
}

/**
 * Quiz question from Claude
 */
export interface QuizQuestion {
  id: string;
  question: string;
  options: QuizOption[];
  correct_answers: string[];
  is_multi_select: boolean;
  hint?: string;
  explanation: string;
}

/**
 * Quiz job record from the API
 */
export interface QuizJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  progress: string;
  error: string | null;
  questions: QuizQuestion[];
  topic_summary: string | null;
  question_count: number;
  generation_time_seconds: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting quiz generation
 */
export interface StartQuizResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  source_name?: string;
  error?: string;
}

/**
 * Response from getting quiz job status
 */
export interface QuizJobStatusResponse {
  success: boolean;
  job?: QuizJob;
  error?: string;
}

/**
 * Response from listing quiz jobs
 */
export interface ListQuizJobsResponse {
  success: boolean;
  jobs: QuizJob[];
  count: number;
  error?: string;
}

class StudioAPI {
  /**
   * Start audio overview generation
   * Educational Note: Non-blocking - returns immediately with job_id
   * Use pollJobStatus to check progress
   */
  async startAudioGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartAudioResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/audio-overview`,
        {
          source_id: sourceId,
          direction: direction || 'Create an engaging audio overview of this content.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting audio generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of an audio generation job
   */
  async getJobStatus(projectId: string, jobId: string): Promise<JobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting job status:', error);
      throw error;
    }
  }

  /**
   * List all audio jobs for a project
   */
  async listJobs(projectId: string, sourceId?: string): Promise<ListJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing jobs:', error);
      throw error;
    }
  }

  /**
   * Check if TTS (ElevenLabs) is configured
   */
  async checkTTSStatus(): Promise<TTSStatusResponse> {
    try {
      const response = await axios.get(`${API_BASE_URL}/studio/tts/status`);
      return response.data;
    } catch (error) {
      console.error('Error checking TTS status:', error);
      return { success: false, configured: false };
    }
  }

  /**
   * Get the full URL for an audio file
   */
  getAudioUrl(projectId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/audio/${filename}`;
  }

  /**
   * Poll job status until complete or error
   * Educational Note: Uses polling with exponential backoff
   *
   * @param projectId - Project ID
   * @param jobId - Job ID to poll
   * @param onProgress - Callback for progress updates
   * @param intervalMs - Initial polling interval (default 2000ms)
   * @param maxAttempts - Max polling attempts (default 120 = ~4 min with backoff)
   */
  async pollJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: AudioJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 120
  ): Promise<AudioJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getJobStatus(projectId, jobId);

      if (!response.success || !response.job) {
        throw new Error(response.error || 'Failed to get job status');
      }

      const job = response.job;

      // Call progress callback
      if (onProgress) {
        onProgress(job);
      }

      // Check if job is complete
      if (job.status === 'ready' || job.status === 'error') {
        return job;
      }

      // Wait before next poll
      await new Promise((resolve) => setTimeout(resolve, currentInterval));

      attempts++;

      // Gentle backoff after first few attempts
      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Audio generation timed out');
  }

  // ===========================================================================
  // Ad Creative Methods
  // ===========================================================================

  /**
   * Start ad creative generation
   */
  async startAdGeneration(
    projectId: string,
    productName: string,
    direction?: string
  ): Promise<StartAdResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/ad-creative`,
        {
          product_name: productName,
          direction: direction || 'Create compelling ad creatives for Facebook and Instagram.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting ad generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of an ad creative job
   */
  async getAdJobStatus(projectId: string, jobId: string): Promise<AdJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/ad-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting ad job status:', error);
      throw error;
    }
  }

  /**
   * List all ad jobs for a project
   */
  async listAdJobs(projectId: string): Promise<ListAdJobsResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/ad-jobs`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing ad jobs:', error);
      throw error;
    }
  }

  /**
   * Check if Gemini is configured
   */
  async checkGeminiStatus(): Promise<TTSStatusResponse> {
    try {
      const response = await axios.get(`${API_BASE_URL}/studio/gemini/status`);
      return response.data;
    } catch (error) {
      console.error('Error checking Gemini status:', error);
      return { success: false, configured: false };
    }
  }

  /**
   * Get the full URL for an ad creative image
   */
  getCreativeUrl(projectId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/creatives/${filename}`;
  }

  /**
   * Poll ad job status until complete or error
   */
  async pollAdJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: AdJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 120
  ): Promise<AdJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getAdJobStatus(projectId, jobId);

      if (!response.success || !response.job) {
        throw new Error(response.error || 'Failed to get job status');
      }

      const job = response.job;

      if (onProgress) {
        onProgress(job);
      }

      if (job.status === 'ready' || job.status === 'error') {
        return job;
      }

      await new Promise((resolve) => setTimeout(resolve, currentInterval));

      attempts++;

      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Ad creative generation timed out');
  }

  // ===========================================================================
  // Flash Card Methods
  // ===========================================================================

  /**
   * Start flash card generation
   */
  async startFlashCardGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartFlashCardsResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/flash-cards`,
        {
          source_id: sourceId,
          direction: direction || 'Create flash cards covering the key concepts.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting flash card generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of a flash card job
   */
  async getFlashCardJobStatus(projectId: string, jobId: string): Promise<FlashCardJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/flash-card-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting flash card job status:', error);
      throw error;
    }
  }

  /**
   * List all flash card jobs for a project
   */
  async listFlashCardJobs(projectId: string, sourceId?: string): Promise<ListFlashCardJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/flash-card-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing flash card jobs:', error);
      throw error;
    }
  }

  /**
   * Poll flash card job status until complete or error
   */
  async pollFlashCardJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: FlashCardJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 60
  ): Promise<FlashCardJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getFlashCardJobStatus(projectId, jobId);

      if (!response.success || !response.job) {
        throw new Error(response.error || 'Failed to get job status');
      }

      const job = response.job;

      if (onProgress) {
        onProgress(job);
      }

      if (job.status === 'ready' || job.status === 'error') {
        return job;
      }

      await new Promise((resolve) => setTimeout(resolve, currentInterval));

      attempts++;

      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Flash card generation timed out');
  }

  // ===========================================================================
  // Mind Map Methods
  // ===========================================================================

  /**
   * Start mind map generation
   */
  async startMindMapGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartMindMapResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/mind-map`,
        {
          source_id: sourceId,
          direction: direction || 'Create a mind map covering the key concepts and their relationships.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting mind map generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of a mind map job
   */
  async getMindMapJobStatus(projectId: string, jobId: string): Promise<MindMapJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/mind-map-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting mind map job status:', error);
      throw error;
    }
  }

  /**
   * List all mind map jobs for a project
   */
  async listMindMapJobs(projectId: string, sourceId?: string): Promise<ListMindMapJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/mind-map-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing mind map jobs:', error);
      throw error;
    }
  }

  /**
   * Poll mind map job status until complete or error
   */
  async pollMindMapJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: MindMapJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 60
  ): Promise<MindMapJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getMindMapJobStatus(projectId, jobId);

      if (!response.success || !response.job) {
        throw new Error(response.error || 'Failed to get job status');
      }

      const job = response.job;

      if (onProgress) {
        onProgress(job);
      }

      if (job.status === 'ready' || job.status === 'error') {
        return job;
      }

      await new Promise((resolve) => setTimeout(resolve, currentInterval));

      attempts++;

      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Mind map generation timed out');
  }

  // ===========================================================================
  // Quiz Methods
  // ===========================================================================

  /**
   * Start quiz generation
   */
  async startQuizGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartQuizResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/quiz`,
        {
          source_id: sourceId,
          direction: direction || 'Create quiz questions covering the key concepts.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting quiz generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of a quiz job
   */
  async getQuizJobStatus(projectId: string, jobId: string): Promise<QuizJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/quiz-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting quiz job status:', error);
      throw error;
    }
  }

  /**
   * List all quiz jobs for a project
   */
  async listQuizJobs(projectId: string, sourceId?: string): Promise<ListQuizJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/quiz-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing quiz jobs:', error);
      throw error;
    }
  }

  /**
   * Poll quiz job status until complete or error
   */
  async pollQuizJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: QuizJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 60
  ): Promise<QuizJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getQuizJobStatus(projectId, jobId);

      if (!response.success || !response.job) {
        throw new Error(response.error || 'Failed to get job status');
      }

      const job = response.job;

      if (onProgress) {
        onProgress(job);
      }

      if (job.status === 'ready' || job.status === 'error') {
        return job;
      }

      await new Promise((resolve) => setTimeout(resolve, currentInterval));

      attempts++;

      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Quiz generation timed out');
  }
}

// Export singleton instance
export const studioAPI = new StudioAPI();
