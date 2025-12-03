/**
 * useEmailGeneration Hook
 * Educational Note: Custom hook for email template generation logic.
 * Handles state management, API calls, and polling.
 */

import { useState } from 'react';
import { emailsAPI, checkGeminiStatus, type EmailJob } from '@/lib/api/studio';
import { useToast } from '../../ui/toast';
import type { StudioSignal } from '../types';

export const useEmailGeneration = (projectId: string) => {
  const { success: showSuccess, error: showError } = useToast();

  // State
  const [savedEmailJobs, setSavedEmailJobs] = useState<EmailJob[]>([]);
  const [currentEmailJob, setCurrentEmailJob] = useState<EmailJob | null>(null);
  const [isGeneratingEmail, setIsGeneratingEmail] = useState(false);
  const [viewingEmailJob, setViewingEmailJob] = useState<EmailJob | null>(null);

  /**
   * Load saved email jobs from backend
   */
  const loadSavedJobs = async () => {
    try {
      const emailResponse = await emailsAPI.listJobs(projectId);
      if (emailResponse.success && emailResponse.jobs) {
        const completedEmails = emailResponse.jobs.filter((job) => job.status === 'ready');
        setSavedEmailJobs(completedEmails);
      }
    } catch (error) {
      console.error('Failed to load saved email jobs:', error);
    }
  };

  /**
   * Handle email template generation
   */
  const handleEmailGeneration = async (signal: StudioSignal) => {
    const sourceId = signal.sources[0]?.source_id;
    if (!sourceId) {
      showError('No source specified for email template generation.');
      return;
    }

    setIsGeneratingEmail(true);
    setCurrentEmailJob(null);

    try {
      // Check Gemini status (email agent uses Gemini for images)
      const geminiStatus = await checkGeminiStatus();
      if (!geminiStatus.configured) {
        showError('Gemini API key not configured. Please add it in App Settings.');
        setIsGeneratingEmail(false);
        return;
      }

      const startResponse = await emailsAPI.startGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start email template generation.');
        setIsGeneratingEmail(false);
        return;
      }

      showSuccess(`Generating email template...`);

      const finalJob = await emailsAPI.pollJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentEmailJob(job)
      );

      setCurrentEmailJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess(`Generated email template: ${finalJob.template_name}!`);
        setSavedEmailJobs((prev) => [finalJob, ...prev]);
        setViewingEmailJob(finalJob); // Open modal to view
      } else if (finalJob.status === 'error') {
        showError(finalJob.error_message || 'Email template generation failed.');
      }
    } catch (error) {
      console.error('Email template generation error:', error);
      showError(error instanceof Error ? error.message : 'Email template generation failed.');
    } finally {
      setIsGeneratingEmail(false);
      setCurrentEmailJob(null);
    }
  };

  return {
    savedEmailJobs,
    currentEmailJob,
    isGeneratingEmail,
    viewingEmailJob,
    setViewingEmailJob,
    loadSavedJobs,
    handleEmailGeneration,
  };
};
