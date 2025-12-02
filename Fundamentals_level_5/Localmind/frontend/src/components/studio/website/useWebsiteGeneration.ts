/**
 * useWebsiteGeneration Hook
 * Educational Note: Custom hook for website generation logic.
 * Handles state management, API calls, and polling.
 */

import { useState } from 'react';
import { studioAPI, type WebsiteJob } from '../../../lib/api/studio';
import { useToast } from '../../ui/toast';
import type { StudioSignal } from '../types';

export const useWebsiteGeneration = (projectId: string) => {
  const { success: showSuccess, error: showError } = useToast();

  // State
  const [savedWebsiteJobs, setSavedWebsiteJobs] = useState<WebsiteJob[]>([]);
  const [currentWebsiteJob, setCurrentWebsiteJob] = useState<WebsiteJob | null>(null);
  const [isGeneratingWebsite, setIsGeneratingWebsite] = useState(false);

  /**
   * Load saved website jobs from backend
   */
  const loadSavedJobs = async () => {
    try {
      const websiteResponse = await studioAPI.listWebsiteJobs(projectId);
      if (websiteResponse.success && websiteResponse.jobs) {
        const completedWebsites = websiteResponse.jobs.filter((job) => job.status === 'ready');
        setSavedWebsiteJobs(completedWebsites);
      }
    } catch (error) {
      console.error('Failed to load saved website jobs:', error);
    }
  };

  /**
   * Handle website generation
   * Educational Note: Websites open in new window automatically after generation
   */
  const handleWebsiteGeneration = async (signal: StudioSignal) => {
    setIsGeneratingWebsite(true);
    setCurrentWebsiteJob(null);

    try {
      const sourceId = signal.sources[0]?.source_id;
      if (!sourceId) {
        showError('No source selected');
        return;
      }

      // Start website generation
      const startResponse = await studioAPI.startWebsiteGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start website generation');
        return;
      }

      // Poll for completion
      const finalJob = await studioAPI.pollWebsiteJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentWebsiteJob(job)
      );

      if (finalJob.status === 'ready') {
        setSavedWebsiteJobs((prev) => [finalJob, ...prev]);
        // Open website in new window automatically
        const previewUrl = studioAPI.getWebsitePreviewUrl(projectId, finalJob.id);
        window.open(`http://localhost:5000${previewUrl}`, '_blank');
        showSuccess('Website generated successfully!');
      } else if (finalJob.status === 'error') {
        showError(finalJob.error_message || 'Website generation failed');
      }
    } catch (error) {
      console.error('Website generation error:', error);
      showError('Website generation failed');
    } finally {
      setIsGeneratingWebsite(false);
      setCurrentWebsiteJob(null);
    }
  };

  /**
   * Open website in new window
   */
  const openWebsite = (jobId: string) => {
    const previewUrl = studioAPI.getWebsitePreviewUrl(projectId, jobId);
    window.open(`http://localhost:5000${previewUrl}`, '_blank');
  };

  /**
   * Download website as ZIP
   */
  const downloadWebsite = (jobId: string) => {
    const downloadUrl = studioAPI.getWebsiteDownloadUrl(projectId, jobId);
    const link = document.createElement('a');
    link.href = `http://localhost:5000${downloadUrl}`;
    link.click();
  };

  return {
    savedWebsiteJobs,
    currentWebsiteJob,
    isGeneratingWebsite,
    loadSavedJobs,
    handleWebsiteGeneration,
    openWebsite,
    downloadWebsite,
  };
};
