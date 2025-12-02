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

/**
 * Social post image info
 */
export interface SocialPostImage {
  filename: string;
  path: string;
  index: number;
}

/**
 * Single social post for one platform
 */
export interface SocialPost {
  platform: 'linkedin' | 'instagram' | 'twitter';
  copy: string;
  hashtags: string[];
  aspect_ratio: string;
  image_prompt: string;
  image: SocialPostImage | null;
  image_url: string | null;
}

/**
 * Social post job record from the API
 */
export interface SocialPostJob {
  id: string;
  topic: string;
  direction: string;
  status: JobStatus;
  progress: string;
  error: string | null;
  posts: SocialPost[];
  topic_summary: string | null;
  post_count: number;
  generation_time_seconds: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting social post generation
 */
export interface StartSocialPostsResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  topic?: string;
  error?: string;
}

/**
 * Response from getting social post job status
 */
export interface SocialPostJobStatusResponse {
  success: boolean;
  job?: SocialPostJob;
  error?: string;
}

/**
 * Response from listing social post jobs
 */
export interface ListSocialPostJobsResponse {
  success: boolean;
  jobs: SocialPostJob[];
  count: number;
  error?: string;
}

/**
 * Infographic image info
 */
export interface InfographicImage {
  filename: string;
  path: string;
  index: number;
}

/**
 * Infographic key section (for display)
 */
export interface InfographicKeySection {
  title: string;
  icon_description: string;
}

/**
 * Infographic job record from the API
 */
export interface InfographicJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  progress: string;
  error: string | null;
  topic_title: string | null;
  topic_summary: string | null;
  key_sections: InfographicKeySection[];
  image: InfographicImage | null;
  image_url: string | null;
  image_prompt: string | null;
  generation_time_seconds: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting infographic generation
 */
export interface StartInfographicResponse {
  success: boolean;
  job_id?: string;
  message?: string;
  source_name?: string;
  error?: string;
}

/**
 * Response from getting infographic job status
 */
export interface InfographicJobStatusResponse {
  success: boolean;
  job?: InfographicJob;
  error?: string;
}

/**
 * Response from listing infographic jobs
 */
export interface ListInfographicJobsResponse {
  success: boolean;
  jobs: InfographicJob[];
  count: number;
  error?: string;
}

// =============================================================================
// Email Template Types
// =============================================================================

/**
 * Email template section plan
 */
export interface EmailSection {
  section_type: 'header' | 'hero' | 'content' | 'product_grid' | 'cta' | 'testimonial' | 'footer';
  section_name: string;
  content_description: string;
  needs_image: boolean;
  image_description?: string;
}

/**
 * Email template color scheme
 */
export interface EmailColorScheme {
  primary: string;
  secondary: string;
  background: string;
  text: string;
  button: string;
}

/**
 * Generated email image info
 */
export interface EmailImage {
  section_name: string;
  filename: string;
  placeholder: string;
  url: string;
}

/**
 * Email template generation job
 */
export interface EmailJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  status_message: string;
  error_message: string | null;
  // Template plan
  template_name: string | null;
  template_type: 'newsletter' | 'promotional' | 'transactional' | 'announcement' | null;
  color_scheme: EmailColorScheme | null;
  sections: EmailSection[];
  layout_notes: string | null;
  // Generated content
  images: EmailImage[];
  html_file: string | null;
  html_url: string | null;
  preview_url: string | null;
  subject_line: string | null;
  preheader_text: string | null;
  // Metadata
  iterations: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting email template generation
 */
export interface StartEmailResponse {
  success: boolean;
  job_id?: string;
  status?: string;
  message?: string;
  error?: string;
}

/**
 * Response from getting email job status
 */
export interface EmailJobStatusResponse {
  success: boolean;
  job?: EmailJob;
  error?: string;
}

/**
 * Response from listing email jobs
 */
export interface ListEmailJobsResponse {
  success: boolean;
  jobs: EmailJob[];
  error?: string;
}

// =============================================================================
// Component Generator Types
// =============================================================================

/**
 * Component variation info
 */
export interface ComponentVariation {
  variation_name: string;
  filename: string;
  description: string;
  preview_url: string;
  char_count: number;
}

/**
 * Planned component variation
 */
export interface PlannedVariation {
  variation_name: string;
  style_approach: string;
  key_features: string[];
}

/**
 * Component generation job
 */
export interface ComponentJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  status_message: string;
  error_message: string | null;
  // Component plan
  component_category: 'button' | 'card' | 'form' | 'navigation' | 'modal' | 'list' | 'grid' | 'hero' | 'pricing' | 'testimonial' | 'footer' | 'other' | null;
  component_description: string | null;
  variations_planned: PlannedVariation[];
  technical_notes: string | null;
  // Generated content
  components: ComponentVariation[];
  usage_notes: string | null;
  // Metadata
  iterations: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting component generation
 */
export interface StartComponentResponse {
  success: boolean;
  job_id?: string;
  status?: string;
  message?: string;
  error?: string;
}

/**
 * Response from getting component job status
 */
export interface ComponentJobStatusResponse {
  success: boolean;
  job?: ComponentJob;
  error?: string;
}

/**
 * Response from listing component jobs
 */
export interface ListComponentJobsResponse {
  success: boolean;
  jobs: ComponentJob[];
  error?: string;
}

// =============================================================================
// Video Generation Types
// =============================================================================

/**
 * Video file information
 */
export interface VideoFile {
  filename: string;
  path: string;
  uri: string;
  preview_url: string;
  download_url: string;
}

/**
 * Video generation job
 */
export interface VideoJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  status_message: string;
  error_message: string | null;

  // Generation parameters
  aspect_ratio: '16:9' | '16:10';
  duration_seconds: number;
  number_of_videos: number;

  // Generated content
  videos: VideoFile[];
  generated_prompt: string | null;

  // Metadata
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting video generation
 */
export interface StartVideoResponse {
  success: boolean;
  job_id?: string;
  status?: string;
  message?: string;
  error?: string;
}

/**
 * Response from getting video job status
 */
export interface VideoJobStatusResponse {
  success: boolean;
  job?: VideoJob;
  error?: string;
}

/**
 * Response from listing video jobs
 */
export interface ListVideoJobsResponse {
  success: boolean;
  jobs: VideoJob[];
  error?: string;
}

// =============================================================================
// Website Generator Types
// =============================================================================

/**
 * Website page information
 */
export interface WebsitePage {
  filename: string;
  page_title: string;
  description: string;
}

/**
 * Website design system
 */
export interface WebsiteDesignSystem {
  primary_color: string;
  secondary_color: string;
  accent_color?: string;
  background_color: string;
  text_color: string;
  font_family: string;
}

/**
 * Generated website image
 */
export interface WebsiteImage {
  purpose: string;
  filename: string;
  placeholder: string;
  url: string;
}

/**
 * Website generation job
 */
export interface WebsiteJob {
  id: string;
  source_id: string;
  source_name: string;
  direction: string;
  status: JobStatus;
  status_message: string;
  error_message: string | null;

  // Plan
  site_type: 'portfolio' | 'business' | 'blog' | 'landing' | 'corporate' | 'personal' | 'ecommerce' | null;
  site_name: string | null;
  pages: WebsitePage[];
  features: string[];
  design_system: WebsiteDesignSystem | null;
  navigation_style: 'fixed' | 'sticky' | 'static' | null;
  images_needed: Array<{
    purpose: string;
    description: string;
    aspect_ratio: string;
  }>;
  layout_notes: string | null;

  // Generated content
  images: WebsiteImage[];
  files: string[];
  pages_created: string[];
  features_implemented: string[];
  cdn_libraries_used: string[];
  summary: string | null;

  // URLs
  preview_url: string | null;
  download_url: string | null;

  // Metadata
  iterations: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Response from starting website generation
 */
export interface StartWebsiteResponse {
  success: boolean;
  job_id?: string;
  status?: string;
  message?: string;
  error?: string;
}

/**
 * Response from getting website job status
 */
export interface WebsiteJobStatusResponse {
  success: boolean;
  job?: WebsiteJob;
  error?: string;
}

/**
 * Response from listing website jobs
 */
export interface ListWebsiteJobsResponse {
  success: boolean;
  jobs: WebsiteJob[];
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

  // ===========================================================================
  // Social Post Methods
  // ===========================================================================

  /**
   * Start social post generation
   */
  async startSocialPostGeneration(
    projectId: string,
    topic: string,
    direction?: string
  ): Promise<StartSocialPostsResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/social-posts`,
        {
          topic: topic,
          direction: direction || 'Create engaging social media posts for this topic.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting social post generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of a social post job
   */
  async getSocialPostJobStatus(projectId: string, jobId: string): Promise<SocialPostJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/social-post-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting social post job status:', error);
      throw error;
    }
  }

  /**
   * List all social post jobs for a project
   */
  async listSocialPostJobs(projectId: string): Promise<ListSocialPostJobsResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/social-post-jobs`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing social post jobs:', error);
      throw error;
    }
  }

  /**
   * Get the full URL for a social post image
   */
  getSocialImageUrl(projectId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/social/${filename}`;
  }

  /**
   * Poll social post job status until complete or error
   */
  async pollSocialPostJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: SocialPostJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 120
  ): Promise<SocialPostJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getSocialPostJobStatus(projectId, jobId);

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

    throw new Error('Social post generation timed out');
  }

  // ===========================================================================
  // Infographic Methods
  // ===========================================================================

  /**
   * Start infographic generation
   */
  async startInfographicGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartInfographicResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/infographic`,
        {
          source_id: sourceId,
          direction: direction || 'Create an informative infographic summarizing the key concepts.',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting infographic generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of an infographic job
   */
  async getInfographicJobStatus(projectId: string, jobId: string): Promise<InfographicJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/infographic-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting infographic job status:', error);
      throw error;
    }
  }

  /**
   * List all infographic jobs for a project
   */
  async listInfographicJobs(projectId: string, sourceId?: string): Promise<ListInfographicJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/infographic-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing infographic jobs:', error);
      throw error;
    }
  }

  /**
   * Get the full URL for an infographic image
   */
  getInfographicUrl(projectId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/infographics/${filename}`;
  }

  /**
   * Poll infographic job status until complete or error
   */
  async pollInfographicJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: InfographicJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 120
  ): Promise<InfographicJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getInfographicJobStatus(projectId, jobId);

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

    throw new Error('Infographic generation timed out');
  }

  // ===========================================================================
  // Email Template Methods
  // ===========================================================================

  /**
   * Start email template generation via email agent
   */
  async startEmailGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartEmailResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/email-template`,
        {
          source_id: sourceId,
          direction: direction || '',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting email template generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of an email template job
   */
  async getEmailJobStatus(projectId: string, jobId: string): Promise<EmailJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/email-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting email job status:', error);
      throw error;
    }
  }

  /**
   * List all email template jobs for a project
   */
  async listEmailJobs(projectId: string, sourceId?: string): Promise<ListEmailJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/email-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing email jobs:', error);
      throw error;
    }
  }

  /**
   * Get the full URL for an email template file (HTML or image)
   */
  getEmailTemplateFileUrl(projectId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/email-templates/${filename}`;
  }

  /**
   * Get the preview URL for an email template
   */
  getEmailPreviewUrl(projectId: string, jobId: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/email-templates/${jobId}/preview`;
  }

  /**
   * Get the download URL for an email template (ZIP)
   */
  getEmailDownloadUrl(projectId: string, jobId: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/email-templates/${jobId}/download`;
  }

  /**
   * Poll email job status until complete or error
   */
  async pollEmailJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: EmailJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 150  // Email generation can take longer (agentic)
  ): Promise<EmailJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getEmailJobStatus(projectId, jobId);

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

      // Gradually increase interval for long-running jobs
      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Email template generation timed out');
  }

  // ===========================================================================
  // Component Generator Methods
  // ===========================================================================

  /**
   * Start component generation via component agent
   */
  async startComponentGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartComponentResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/components`,
        {
          source_id: sourceId,
          direction: direction || '',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting component generation:', error);
      throw error;
    }
  }

  /**
   * Get the status of a component generation job
   */
  async getComponentJobStatus(projectId: string, jobId: string): Promise<ComponentJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/component-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting component job status:', error);
      throw error;
    }
  }

  /**
   * List all component generation jobs for a project
   */
  async listComponentJobs(projectId: string, sourceId?: string): Promise<ListComponentJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/component-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing component jobs:', error);
      throw error;
    }
  }

  /**
   * Get the preview URL for a component
   */
  getComponentPreviewUrl(projectId: string, jobId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/components/${jobId}/preview/${filename}`;
  }

  /**
   * Poll component job status until complete or error
   */
  async pollComponentJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: ComponentJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 120  // Component generation is simpler than websites
  ): Promise<ComponentJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getComponentJobStatus(projectId, jobId);

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

      // Gradually increase interval for long-running jobs
      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Component generation timed out');
  }

  // ===========================================================================
  // Website Generator Methods
  // ===========================================================================

  /**
   * Start website generation (background task)
   * Educational Note: Non-blocking - returns immediately with job_id
   */
  async startWebsiteGeneration(
    projectId: string,
    sourceId: string,
    direction?: string
  ): Promise<StartWebsiteResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/website`,
        {
          source_id: sourceId,
          direction: direction || '',
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting website generation:', error);
      throw error;
    }
  }

  /**
   * Get website job status
   */
  async getWebsiteJobStatus(projectId: string, jobId: string): Promise<WebsiteJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/website-jobs/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting website job status:', error);
      throw error;
    }
  }

  /**
   * List all website jobs for a project, optionally filtered by source
   */
  async listWebsiteJobs(projectId: string, sourceId?: string): Promise<ListWebsiteJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/website-jobs`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing website jobs:', error);
      throw error;
    }
  }

  /**
   * Get the preview URL for a website (opens in new window)
   */
  getWebsitePreviewUrl(projectId: string, jobId: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/websites/${jobId}/preview`;
  }

  /**
   * Get the download URL for a website (ZIP with all files)
   */
  getWebsiteDownloadUrl(projectId: string, jobId: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/websites/${jobId}/download`;
  }

  /**
   * Poll website job status until complete or error
   */
  async pollWebsiteJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: WebsiteJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 200  // Websites can take longer (multi-file, iterative)
  ): Promise<WebsiteJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getWebsiteJobStatus(projectId, jobId);

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

      // Gradually increase interval for long-running jobs
      if (attempts > 5 && currentInterval < 5000) {
        currentInterval = Math.min(currentInterval * 1.2, 5000);
      }
    }

    throw new Error('Website generation timed out');
  }

  // ===========================================================================
  // Video Generation Methods
  // ===========================================================================

  /**
   * Start video generation (background task)
   * Educational Note: Non-blocking - returns immediately with job_id
   * Uses Claude to generate optimized video prompt, then Google Veo for video
   */
  async startVideoGeneration(
    projectId: string,
    sourceId: string,
    direction?: string,
    aspectRatio: '16:9' | '16:10' = '16:9',
    durationSeconds: number = 8,
    numberOfVideos: number = 1
  ): Promise<StartVideoResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/projects/${projectId}/studio/videos`,
        {
          source_id: sourceId,
          direction: direction || '',
          aspect_ratio: aspectRatio,
          duration_seconds: durationSeconds,
          number_of_videos: numberOfVideos,
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error starting video generation:', error);
      throw error;
    }
  }

  /**
   * Get video job status
   */
  async getVideoJobStatus(projectId: string, jobId: string): Promise<VideoJobStatusResponse> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/videos/${jobId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error getting video job status:', error);
      throw error;
    }
  }

  /**
   * List all video jobs for a project, optionally filtered by source
   */
  async listVideoJobs(projectId: string, sourceId?: string): Promise<ListVideoJobsResponse> {
    try {
      const params = sourceId ? { source_id: sourceId } : {};
      const response = await axios.get(
        `${API_BASE_URL}/projects/${projectId}/studio/videos`,
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        return error.response.data;
      }
      console.error('Error listing video jobs:', error);
      throw error;
    }
  }

  /**
   * Get the preview URL for a video (streams video in browser)
   */
  getVideoPreviewUrl(projectId: string, jobId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/videos/${jobId}/preview/${filename}`;
  }

  /**
   * Get the download URL for a video
   */
  getVideoDownloadUrl(projectId: string, jobId: string, filename: string): string {
    return `${API_BASE_URL}/projects/${projectId}/studio/videos/${jobId}/download/${filename}`;
  }

  /**
   * Poll video job status until complete or error
   * Educational Note: Video generation can take 10-20 minutes with Google Veo
   */
  async pollVideoJobStatus(
    projectId: string,
    jobId: string,
    onProgress?: (job: VideoJob) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 600  // Up to 20 minutes with 2s polling
  ): Promise<VideoJob> {
    let attempts = 0;
    let currentInterval = intervalMs;

    while (attempts < maxAttempts) {
      const response = await this.getVideoJobStatus(projectId, jobId);

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

      // Gradually increase interval for long-running jobs
      if (attempts > 5 && currentInterval < 10000) {
        currentInterval = Math.min(currentInterval * 1.2, 10000);
      }
    }

    throw new Error('Video generation timed out');
  }
}

// Export singleton instance
export const studioAPI = new StudioAPI();
