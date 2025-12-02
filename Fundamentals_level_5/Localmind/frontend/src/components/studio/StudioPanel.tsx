/**
 * StudioPanel Component
 * Educational Note: Main orchestrator for the Studio panel.
 * Receives signals from chat and handles generation workflows.
 * Shows a picker when multiple signals exist for the same studio item.
 */

import React, { useState, useEffect } from 'react';
import { StudioHeader } from './StudioHeader';
import { StudioToolsList } from './StudioToolsList';
import { generationOptions, type StudioSignal, type StudioItemId } from './types';
import { ScrollArea } from '../ui/scroll-area';
import { useToast } from '../ui/toast';
import { useEmailGeneration } from './email';
import { useWebsiteGeneration } from './website';
import { useInfographicGeneration } from './infographic';
import { useFlashCardGeneration } from './flashcards';
import { useAdGeneration } from './ads';
import { useSocialPostGeneration } from './social';
import { useAudioGeneration } from './audio';
import { useMindMapGeneration } from './mindmap';
import { useQuizGeneration } from './quiz';
import { StudioCollapsedView } from './StudioCollapsedView';
import { StudioSignalPicker } from './StudioSignalPicker';
import { StudioProgressIndicators } from './StudioProgressIndicators';
import { StudioGeneratedContent } from './StudioGeneratedContent';
import { StudioModals } from './StudioModals';

interface StudioPanelProps {
  projectId: string;
  signals: StudioSignal[];
  isCollapsed?: boolean;
  onExpand?: () => void;
}

export const StudioPanel: React.FC<StudioPanelProps> = ({
  projectId,
  signals,
  isCollapsed,
  onExpand,
}) => {
  const { success: showSuccess } = useToast();

  // State for signal picker dialog
  const [pickerOpen, setPickerOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<StudioItemId | null>(null);
  const [selectedSignals, setSelectedSignals] = useState<StudioSignal[]>([]);

  // Audio generation hook
  const {
    savedAudioJobs,
    currentAudioJob,
    isGeneratingAudio,
    playingJobId,
    audioRef,
    handleAudioEnd,
    loadSavedJobs: loadSavedAudioJobs,
    handleAudioGeneration,
    playAudio,
    pauseAudio,
    downloadAudio,
  } = useAudioGeneration(projectId);

  // Ad generation hook
  const {
    savedAdJobs,
    currentAdJob,
    isGeneratingAd,
    viewingAdJob,
    setViewingAdJob,
    loadSavedJobs: loadSavedAdJobs,
    handleAdGeneration,
  } = useAdGeneration(projectId);

  // Flash card generation hook
  const {
    savedFlashCardJobs,
    currentFlashCardJob,
    isGeneratingFlashCards,
    viewingFlashCardJob,
    setViewingFlashCardJob,
    loadSavedJobs: loadSavedFlashCardJobs,
    handleFlashCardGeneration,
  } = useFlashCardGeneration(projectId);

  // Mind map generation hook
  const {
    savedMindMapJobs,
    currentMindMapJob,
    isGeneratingMindMap,
    viewingMindMapJob,
    setViewingMindMapJob,
    loadSavedJobs: loadSavedMindMapJobs,
    handleMindMapGeneration,
  } = useMindMapGeneration(projectId);

  // Quiz generation hook
  const {
    savedQuizJobs,
    currentQuizJob,
    isGeneratingQuiz,
    viewingQuizJob,
    setViewingQuizJob,
    loadSavedJobs: loadSavedQuizJobs,
    handleQuizGeneration,
  } = useQuizGeneration(projectId);

  // Social post generation hook
  const {
    savedSocialPostJobs,
    currentSocialPostJob,
    isGeneratingSocialPosts,
    viewingSocialPostJob,
    setViewingSocialPostJob,
    loadSavedJobs: loadSavedSocialPostJobs,
    handleSocialPostGeneration,
  } = useSocialPostGeneration(projectId);

  // Infographic generation hook
  const {
    savedInfographicJobs,
    currentInfographicJob,
    isGeneratingInfographic,
    viewingInfographicJob,
    setViewingInfographicJob,
    loadSavedJobs: loadSavedInfographicJobs,
    handleInfographicGeneration,
  } = useInfographicGeneration(projectId);

  // Email generation hook
  const {
    savedEmailJobs,
    currentEmailJob,
    isGeneratingEmail,
    viewingEmailJob,
    setViewingEmailJob,
    loadSavedJobs: loadSavedEmailJobs,
    handleEmailGeneration,
  } = useEmailGeneration(projectId);

  // Website generation hook
  const {
    savedWebsiteJobs,
    currentWebsiteJob,
    isGeneratingWebsite,
    loadSavedJobs: loadSavedWebsiteJobs,
    handleWebsiteGeneration,
    openWebsite,
    downloadWebsite,
  } = useWebsiteGeneration(projectId);
  // Load saved jobs on mount
  useEffect(() => {
    const loadSavedJobs = async () => {
      try {
        // Load audio jobs
        await loadSavedAudioJobs();

        // Load ad jobs
        await loadSavedAdJobs();

        // Load flash card jobs
        await loadSavedFlashCardJobs();

        // Load mind map jobs
        await loadSavedMindMapJobs();

        // Load quiz jobs
        await loadSavedQuizJobs();

        // Load social post jobs
        await loadSavedSocialPostJobs();

        // Load infographic jobs
        await loadSavedInfographicJobs();

        // Load email template jobs
        await loadSavedEmailJobs();

        // Load saved website jobs
        await loadSavedWebsiteJobs();

      } catch (error) {
        console.error('Failed to load saved jobs:', error);
      }
    };
    loadSavedJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  /**
   * Handle generation request
   * Educational Note: If multiple signals exist for an item, show picker.
   * If only one signal, trigger generation directly.
   */
  const handleGenerate = (optionId: StudioItemId, itemSignals: StudioSignal[]) => {
    if (itemSignals.length === 0) return;

    if (itemSignals.length === 1) {
      // Single signal - generate directly
      triggerGeneration(optionId, itemSignals[0]);
    } else {
      // Multiple signals - show picker
      setSelectedItem(optionId);
      setSelectedSignals(itemSignals);
      setPickerOpen(true);
    }
  };

  /**
   * Trigger the actual generation workflow
   * Educational Note: This calls the backend studio generator
   */
  const triggerGeneration = async (optionId: StudioItemId, signal: StudioSignal) => {
    setPickerOpen(false);

    if (optionId === 'audio_overview') {
      await handleAudioGeneration(signal);
    } else if (optionId === 'ads_creative') {
      await handleAdGeneration(signal);
    } else if (optionId === 'flash_cards') {
      await handleFlashCardGeneration(signal);
    } else if (optionId === 'mind_map') {
      await handleMindMapGeneration(signal);
    } else if (optionId === 'quiz') {
      await handleQuizGeneration(signal);
    } else if (optionId === 'social') {
      await handleSocialPostGeneration(signal);
    } else if (optionId === 'infographics') {
      await handleInfographicGeneration(signal);
    } else if (optionId === 'email_templates') {
      await handleEmailGeneration(signal);
    } else if (optionId === 'website') {
      await handleWebsiteGeneration(signal);
    } else {
      showSuccess(`${getItemTitle(optionId)} generation is coming soon!`);
    }
  };

  /**
   * Get display name for a studio item
   */
  const getItemTitle = (itemId: StudioItemId): string => {
    const option = generationOptions.find((opt) => opt.id === itemId);
    return option?.title || itemId;
  };

  /**
   * Get icon for a studio item
   */
  const getItemIcon = (itemId: StudioItemId) => {
    const option = generationOptions.find((opt) => opt.id === itemId);
    return option?.icon;
  };

  // Collapsed view - show icon bar with action icons
  if (isCollapsed) {
    return (
      <StudioCollapsedView
        signals={signals}
        onExpand={onExpand!}
        onGenerate={handleGenerate}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      <StudioHeader />

      {/* Hidden audio element for playback */}
      <audio
        ref={audioRef}
        onEnded={handleAudioEnd}
        onPause={() => playingJobId && audioRef.current?.pause()}
      />

      {/* TOP HALF: Generation Tools */}
      <div className="flex-1 min-h-0 border-b">
        <StudioToolsList signals={signals} onGenerate={handleGenerate} />
      </div>

      {/* BOTTOM HALF: Generated Outputs */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="px-3 py-2 border-b">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Generated Content
          </h3>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-3 space-y-2">
            {/* Progress Indicators */}
            <StudioProgressIndicators
              isGeneratingAudio={isGeneratingAudio}
              currentAudioJob={currentAudioJob}
              isGeneratingAd={isGeneratingAd}
              currentAdJob={currentAdJob}
              isGeneratingFlashCards={isGeneratingFlashCards}
              currentFlashCardJob={currentFlashCardJob}
              isGeneratingMindMap={isGeneratingMindMap}
              currentMindMapJob={currentMindMapJob}
              isGeneratingWebsite={isGeneratingWebsite}
              currentWebsiteJob={currentWebsiteJob}
              isGeneratingQuiz={isGeneratingQuiz}
              currentQuizJob={currentQuizJob}
              isGeneratingSocialPosts={isGeneratingSocialPosts}
              currentSocialPostJob={currentSocialPostJob}
              isGeneratingInfographic={isGeneratingInfographic}
              currentInfographicJob={currentInfographicJob}
              isGeneratingEmail={isGeneratingEmail}
              currentEmailJob={currentEmailJob}
            />

            {/* Generated Content List */}
            <StudioGeneratedContent
              signals={signals}
              savedAudioJobs={savedAudioJobs}
              playingJobId={playingJobId}
              playAudio={playAudio}
              pauseAudio={pauseAudio}
              downloadAudio={downloadAudio}
              savedAdJobs={savedAdJobs}
              setViewingAdJob={setViewingAdJob}
              savedFlashCardJobs={savedFlashCardJobs}
              setViewingFlashCardJob={setViewingFlashCardJob}
              savedMindMapJobs={savedMindMapJobs}
              setViewingMindMapJob={setViewingMindMapJob}
              savedWebsiteJobs={savedWebsiteJobs}
              openWebsite={openWebsite}
              downloadWebsite={downloadWebsite}
              savedQuizJobs={savedQuizJobs}
              setViewingQuizJob={setViewingQuizJob}
              savedSocialPostJobs={savedSocialPostJobs}
              setViewingSocialPostJob={setViewingSocialPostJob}
              savedInfographicJobs={savedInfographicJobs}
              setViewingInfographicJob={setViewingInfographicJob}
              savedEmailJobs={savedEmailJobs}
              setViewingEmailJob={setViewingEmailJob}
            />
          </div>
        </ScrollArea>
      </div>

      {/* Signal Picker Dialog */}
      <StudioSignalPicker
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        selectedItem={selectedItem}
        selectedSignals={selectedSignals}
        onSelectSignal={triggerGeneration}
        getItemTitle={getItemTitle}
        getItemIcon={getItemIcon}
      />

      {/* All Studio Modals */}
      <StudioModals
        projectId={projectId}
        viewingAdJob={viewingAdJob}
        setViewingAdJob={setViewingAdJob}
        viewingFlashCardJob={viewingFlashCardJob}
        setViewingFlashCardJob={setViewingFlashCardJob}
        viewingMindMapJob={viewingMindMapJob}
        setViewingMindMapJob={setViewingMindMapJob}
        viewingQuizJob={viewingQuizJob}
        setViewingQuizJob={setViewingQuizJob}
        viewingSocialPostJob={viewingSocialPostJob}
        setViewingSocialPostJob={setViewingSocialPostJob}
        viewingInfographicJob={viewingInfographicJob}
        setViewingInfographicJob={setViewingInfographicJob}
        viewingEmailJob={viewingEmailJob}
        setViewingEmailJob={setViewingEmailJob}
      />
    </div>
  );
};
