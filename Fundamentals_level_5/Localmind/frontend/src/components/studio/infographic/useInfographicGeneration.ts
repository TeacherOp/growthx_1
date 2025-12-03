/**
 * useInfographicGeneration Hook
 * Educational Note: Custom hook for infographic generation logic.
 * Handles state management, API calls, and polling.
 */

import { useState } from 'react';
import { infographicsAPI, checkGeminiStatus, type InfographicJob } from '@/lib/api/studio';
import { useToast } from '../../ui/toast';
import type { StudioSignal } from '../types';

export const useInfographicGeneration = (projectId: string) => {
  const { success: showSuccess, error: showError } = useToast();

  // State
  const [savedInfographicJobs, setSavedInfographicJobs] = useState<InfographicJob[]>([]);
  const [currentInfographicJob, setCurrentInfographicJob] = useState<InfographicJob | null>(null);
  const [isGeneratingInfographic, setIsGeneratingInfographic] = useState(false);
  const [viewingInfographicJob, setViewingInfographicJob] = useState<InfographicJob | null>(null);

  /**
   * Load saved infographic jobs from backend
   */
  const loadSavedJobs = async () => {
    try {
      const infographicResponse = await infographicsAPI.listJobs(projectId);
      if (infographicResponse.success && infographicResponse.jobs) {
        const completedInfographics = infographicResponse.jobs.filter((job) => job.status === 'ready');
        setSavedInfographicJobs(completedInfographics);
      }
    } catch (error) {
      console.error('Failed to load saved infographic jobs:', error);
    }
  };

  /**
   * Handle infographic generation
   */
  const handleInfographicGeneration = async (signal: StudioSignal) => {
    const sourceId = signal.sources[0]?.source_id;
    if (!sourceId) {
      showError('No source specified for infographic generation.');
      return;
    }

    setIsGeneratingInfographic(true);
    setCurrentInfographicJob(null);

    try {
      const geminiStatus = await checkGeminiStatus();
      if (!geminiStatus.configured) {
        showError('Gemini API key not configured. Please add it in App Settings.');
        setIsGeneratingInfographic(false);
        return;
      }

      const startResponse = await infographicsAPI.startGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start infographic generation.');
        setIsGeneratingInfographic(false);
        return;
      }

      showSuccess(`Generating infographic for ${startResponse.source_name}...`);

      const finalJob = await infographicsAPI.pollJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentInfographicJob(job)
      );

      setCurrentInfographicJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess(`Generated infographic: ${finalJob.topic_title}!`);
        setSavedInfographicJobs((prev) => [finalJob, ...prev]);
        setViewingInfographicJob(finalJob); // Open modal to view
      } else if (finalJob.status === 'error') {
        showError(finalJob.error || 'Infographic generation failed.');
      }
    } catch (error) {
      console.error('Infographic generation error:', error);
      showError(error instanceof Error ? error.message : 'Infographic generation failed.');
    } finally {
      setIsGeneratingInfographic(false);
      setCurrentInfographicJob(null);
    }
  };

  return {
    savedInfographicJobs,
    currentInfographicJob,
    isGeneratingInfographic,
    viewingInfographicJob,
    setViewingInfographicJob,
    loadSavedJobs,
    handleInfographicGeneration,
  };
};
