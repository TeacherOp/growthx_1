/**
 * StudioPanel Component
 * Educational Note: Main orchestrator for the Studio panel.
 * Receives signals from chat and handles generation workflows.
 * Shows a picker when multiple signals exist for the same studio item.
 */

import React, { useState, useRef, useEffect } from 'react';
import { StudioHeader } from './StudioHeader';
import { StudioToolsList } from './StudioToolsList';
import {
  generationOptions,
  type StudioSignal,
  type StudioItemId,
} from './types';
import { ScrollArea } from '../ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import { MagicWand, CaretLeft, CaretRight, Play, Pause, SpinnerGap, DownloadSimple, SpeakerHigh, Image, Cards, ArrowsClockwise, TreeStructure, Exam } from '@phosphor-icons/react';
import { studioAPI, type AudioJob, type AdJob, type FlashCardJob, type MindMapJob, type QuizJob } from '../../lib/api/studio';
import { useToast } from '../ui/toast';
import { MindMapViewer } from './MindMapViewer';
import { QuizViewer } from './QuizViewer';

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
  const { success: showSuccess, error: showError } = useToast();

  // State for signal picker dialog
  const [pickerOpen, setPickerOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<StudioItemId | null>(null);
  const [selectedSignals, setSelectedSignals] = useState<StudioSignal[]>([]);

  // State for audio - persisted jobs and current generation
  const [savedAudioJobs, setSavedAudioJobs] = useState<AudioJob[]>([]);
  const [currentAudioJob, setCurrentAudioJob] = useState<AudioJob | null>(null);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [playingJobId, setPlayingJobId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // State for ad creatives
  const [savedAdJobs, setSavedAdJobs] = useState<AdJob[]>([]);
  const [currentAdJob, setCurrentAdJob] = useState<AdJob | null>(null);
  const [isGeneratingAd, setIsGeneratingAd] = useState(false);
  const [viewingAdJob, setViewingAdJob] = useState<AdJob | null>(null);

  // State for flash cards
  const [savedFlashCardJobs, setSavedFlashCardJobs] = useState<FlashCardJob[]>([]);
  const [currentFlashCardJob, setCurrentFlashCardJob] = useState<FlashCardJob | null>(null);
  const [isGeneratingFlashCards, setIsGeneratingFlashCards] = useState(false);
  const [viewingFlashCardJob, setViewingFlashCardJob] = useState<FlashCardJob | null>(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isCardFlipped, setIsCardFlipped] = useState(false);

  // State for mind maps
  const [savedMindMapJobs, setSavedMindMapJobs] = useState<MindMapJob[]>([]);
  const [currentMindMapJob, setCurrentMindMapJob] = useState<MindMapJob | null>(null);
  const [isGeneratingMindMap, setIsGeneratingMindMap] = useState(false);
  const [viewingMindMapJob, setViewingMindMapJob] = useState<MindMapJob | null>(null);

  // State for quizzes
  const [savedQuizJobs, setSavedQuizJobs] = useState<QuizJob[]>([]);
  const [currentQuizJob, setCurrentQuizJob] = useState<QuizJob | null>(null);
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [viewingQuizJob, setViewingQuizJob] = useState<QuizJob | null>(null);

  // Load saved jobs on mount
  useEffect(() => {
    const loadSavedJobs = async () => {
      try {
        // Load audio jobs
        const audioResponse = await studioAPI.listJobs(projectId);
        if (audioResponse.success && audioResponse.jobs) {
          const completedAudio = audioResponse.jobs.filter((job) => job.status === 'ready');
          setSavedAudioJobs(completedAudio);
        }

        // Load ad jobs
        const adResponse = await studioAPI.listAdJobs(projectId);
        if (adResponse.success && adResponse.jobs) {
          const completedAds = adResponse.jobs.filter((job) => job.status === 'ready');
          setSavedAdJobs(completedAds);
        }

        // Load flash card jobs
        const flashCardResponse = await studioAPI.listFlashCardJobs(projectId);
        if (flashCardResponse.success && flashCardResponse.jobs) {
          const completedFlashCards = flashCardResponse.jobs.filter((job) => job.status === 'ready');
          setSavedFlashCardJobs(completedFlashCards);
        }

        // Load mind map jobs
        const mindMapResponse = await studioAPI.listMindMapJobs(projectId);
        if (mindMapResponse.success && mindMapResponse.jobs) {
          const completedMindMaps = mindMapResponse.jobs.filter((job) => job.status === 'ready');
          setSavedMindMapJobs(completedMindMaps);
        }

        // Load quiz jobs
        const quizResponse = await studioAPI.listQuizJobs(projectId);
        if (quizResponse.success && quizResponse.jobs) {
          const completedQuizzes = quizResponse.jobs.filter((job) => job.status === 'ready');
          setSavedQuizJobs(completedQuizzes);
        }
      } catch (error) {
        console.error('Failed to load saved jobs:', error);
      }
    };
    loadSavedJobs();
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
    } else {
      showSuccess(`${getItemTitle(optionId)} generation is coming soon!`);
    }
  };

  /**
   * Handle audio overview generation
   */
  const handleAudioGeneration = async (signal: StudioSignal) => {
    const sourceId = signal.sources[0]?.source_id;
    if (!sourceId) {
      showError('No source specified for audio generation.');
      return;
    }

    setIsGeneratingAudio(true);
    setCurrentAudioJob(null);

    try {
      const ttsStatus = await studioAPI.checkTTSStatus();
      if (!ttsStatus.configured) {
        showError('ElevenLabs API key not configured. Please add it in App Settings.');
        setIsGeneratingAudio(false);
        return;
      }

      const startResponse = await studioAPI.startAudioGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start audio generation.');
        setIsGeneratingAudio(false);
        return;
      }

      showSuccess(`Generating audio for ${startResponse.source_name}...`);

      const finalJob = await studioAPI.pollJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentAudioJob(job)
      );

      setCurrentAudioJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess('Your audio overview is ready to play!');
        setSavedAudioJobs((prev) => [finalJob, ...prev]);
      } else if (finalJob.status === 'error') {
        showError(finalJob.error || 'Audio generation failed.');
      }
    } catch (error) {
      console.error('Audio generation error:', error);
      showError(error instanceof Error ? error.message : 'Audio generation failed.');
    } finally {
      setIsGeneratingAudio(false);
      setCurrentAudioJob(null);
    }
  };

  /**
   * Handle ad creative generation
   */
  const handleAdGeneration = async (signal: StudioSignal) => {
    // Extract product name from direction
    const productName = signal.direction || 'Product';

    setIsGeneratingAd(true);
    setCurrentAdJob(null);

    try {
      const geminiStatus = await studioAPI.checkGeminiStatus();
      if (!geminiStatus.configured) {
        showError('Gemini API key not configured. Please add it in App Settings.');
        setIsGeneratingAd(false);
        return;
      }

      const startResponse = await studioAPI.startAdGeneration(
        projectId,
        productName,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start ad generation.');
        setIsGeneratingAd(false);
        return;
      }

      showSuccess(`Generating ad creatives...`);

      const finalJob = await studioAPI.pollAdJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentAdJob(job)
      );

      setCurrentAdJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess(`Generated ${finalJob.images.length} ad creatives!`);
        setSavedAdJobs((prev) => [finalJob, ...prev]);
        setViewingAdJob(finalJob); // Open modal to view
      } else if (finalJob.status === 'error') {
        showError(finalJob.error || 'Ad generation failed.');
      }
    } catch (error) {
      console.error('Ad generation error:', error);
      showError(error instanceof Error ? error.message : 'Ad generation failed.');
    } finally {
      setIsGeneratingAd(false);
      setCurrentAdJob(null);
    }
  };

  /**
   * Handle flash card generation
   */
  const handleFlashCardGeneration = async (signal: StudioSignal) => {
    const sourceId = signal.sources[0]?.source_id;
    if (!sourceId) {
      showError('No source specified for flash card generation.');
      return;
    }

    setIsGeneratingFlashCards(true);
    setCurrentFlashCardJob(null);

    try {
      const startResponse = await studioAPI.startFlashCardGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start flash card generation.');
        setIsGeneratingFlashCards(false);
        return;
      }

      showSuccess(`Generating flash cards for ${startResponse.source_name}...`);

      const finalJob = await studioAPI.pollFlashCardJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentFlashCardJob(job)
      );

      setCurrentFlashCardJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess(`Generated ${finalJob.card_count} flash cards!`);
        setSavedFlashCardJobs((prev) => [finalJob, ...prev]);
        setViewingFlashCardJob(finalJob); // Open modal to view
        setCurrentCardIndex(0); // Start at first card
        setIsCardFlipped(false); // Reset flip state
      } else if (finalJob.status === 'error') {
        showError(finalJob.error || 'Flash card generation failed.');
      }
    } catch (error) {
      console.error('Flash card generation error:', error);
      showError(error instanceof Error ? error.message : 'Flash card generation failed.');
    } finally {
      setIsGeneratingFlashCards(false);
      setCurrentFlashCardJob(null);
    }
  };

  /**
   * Handle mind map generation
   */
  const handleMindMapGeneration = async (signal: StudioSignal) => {
    const sourceId = signal.sources[0]?.source_id;
    if (!sourceId) {
      showError('No source specified for mind map generation.');
      return;
    }

    setIsGeneratingMindMap(true);
    setCurrentMindMapJob(null);

    try {
      const startResponse = await studioAPI.startMindMapGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start mind map generation.');
        setIsGeneratingMindMap(false);
        return;
      }

      showSuccess(`Generating mind map for ${startResponse.source_name}...`);

      const finalJob = await studioAPI.pollMindMapJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentMindMapJob(job)
      );

      setCurrentMindMapJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess(`Generated mind map with ${finalJob.node_count} nodes!`);
        setSavedMindMapJobs((prev) => [finalJob, ...prev]);
        setViewingMindMapJob(finalJob); // Open modal to view
      } else if (finalJob.status === 'error') {
        showError(finalJob.error || 'Mind map generation failed.');
      }
    } catch (error) {
      console.error('Mind map generation error:', error);
      showError(error instanceof Error ? error.message : 'Mind map generation failed.');
    } finally {
      setIsGeneratingMindMap(false);
      setCurrentMindMapJob(null);
    }
  };

  /**
   * Handle quiz generation
   */
  const handleQuizGeneration = async (signal: StudioSignal) => {
    const sourceId = signal.sources[0]?.source_id;
    if (!sourceId) {
      showError('No source specified for quiz generation.');
      return;
    }

    setIsGeneratingQuiz(true);
    setCurrentQuizJob(null);

    try {
      const startResponse = await studioAPI.startQuizGeneration(
        projectId,
        sourceId,
        signal.direction
      );

      if (!startResponse.success || !startResponse.job_id) {
        showError(startResponse.error || 'Failed to start quiz generation.');
        setIsGeneratingQuiz(false);
        return;
      }

      showSuccess(`Generating quiz for ${startResponse.source_name}...`);

      const finalJob = await studioAPI.pollQuizJobStatus(
        projectId,
        startResponse.job_id,
        (job) => setCurrentQuizJob(job)
      );

      setCurrentQuizJob(finalJob);

      if (finalJob.status === 'ready') {
        showSuccess(`Generated ${finalJob.question_count} quiz questions!`);
        setSavedQuizJobs((prev) => [finalJob, ...prev]);
        setViewingQuizJob(finalJob); // Open modal to view
      } else if (finalJob.status === 'error') {
        showError(finalJob.error || 'Quiz generation failed.');
      }
    } catch (error) {
      console.error('Quiz generation error:', error);
      showError(error instanceof Error ? error.message : 'Quiz generation failed.');
    } finally {
      setIsGeneratingQuiz(false);
      setCurrentQuizJob(null);
    }
  };

  /**
   * Toggle current card flip
   */
  const toggleCardFlip = () => {
    setIsCardFlipped((prev) => !prev);
  };

  /**
   * Navigate to next card
   */
  const nextCard = () => {
    if (viewingFlashCardJob && currentCardIndex < viewingFlashCardJob.cards.length - 1) {
      setCurrentCardIndex((prev) => prev + 1);
      setIsCardFlipped(false); // Reset flip state for new card
    }
  };

  /**
   * Navigate to previous card
   */
  const prevCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex((prev) => prev - 1);
      setIsCardFlipped(false); // Reset flip state for new card
    }
  };

  /**
   * Play a specific audio job
   */
  const playAudio = (job: AudioJob) => {
    if (!job.audio_url) return;

    // Stop current playback if different job
    if (audioRef.current && playingJobId !== job.id) {
      audioRef.current.pause();
    }

    // Set the source and play
    if (audioRef.current) {
      audioRef.current.src = `http://localhost:5000${job.audio_url}`;
      audioRef.current.play();
      setPlayingJobId(job.id);
    }
  };

  /**
   * Pause current playback
   */
  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setPlayingJobId(null);
  };

  /**
   * Handle audio end
   */
  const handleAudioEnd = () => {
    setPlayingJobId(null);
  };

  /**
   * Download audio file
   */
  const downloadAudio = (job: AudioJob) => {
    if (!job.audio_url) return;
    const link = document.createElement('a');
    link.href = `http://localhost:5000${job.audio_url}`;
    link.download = job.audio_filename || 'audio_overview.mp3';
    link.click();
  };

  /**
   * Format duration for display
   */
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
      <TooltipProvider delayDuration={100}>
        <div className="h-full flex flex-col items-center py-3 bg-card">
          {/* Studio header icon */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onExpand}
                className="p-2 rounded-lg hover:bg-muted transition-colors mb-2"
              >
                <MagicWand size={20} className="text-primary" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p>Studio</p>
            </TooltipContent>
          </Tooltip>

          {/* Expand button */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onExpand}
                className="p-1.5 rounded-lg hover:bg-muted transition-colors mb-3"
              >
                <CaretLeft size={14} className="text-muted-foreground" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p>Expand panel</p>
            </TooltipContent>
          </Tooltip>

          {/* Action icons - only show active items */}
          <ScrollArea className="flex-1 w-full">
            <div className="flex flex-col items-center gap-1 px-1">
              {generationOptions.map((option) => {
                const itemSignals = signals.filter((s) => s.studio_item === option.id);
                const isActive = itemSignals.length > 0;
                const IconComponent = option.icon;

                return (
                  <Tooltip key={option.id}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => isActive && handleGenerate(option.id, itemSignals)}
                        className={`p-2 rounded-lg transition-colors w-full flex justify-center relative ${
                          isActive
                            ? 'hover:bg-muted'
                            : 'opacity-30 cursor-default'
                        }`}
                        disabled={!isActive}
                      >
                        <IconComponent
                          size={18}
                          className={isActive ? 'text-primary' : 'text-muted-foreground'}
                        />
                        {/* Active indicator */}
                        {isActive && (
                          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-primary rounded-full" />
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{option.title}</p>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </ScrollArea>
        </div>
      </TooltipProvider>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <StudioHeader />

      {/* Hidden audio element for playback */}
      <audio
        ref={audioRef}
        onEnded={handleAudioEnd}
        onPause={() => setPlayingJobId(null)}
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
            {/* Audio Generation Progress */}
            {isGeneratingAudio && currentAudioJob && (
              <div className="p-2 bg-primary/5 rounded-md border border-primary/20 overflow-hidden">
                <div className="flex items-center gap-2">
                  <SpinnerGap size={14} className="animate-spin text-primary flex-shrink-0" />
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <p className="text-xs font-medium truncate">
                      {currentAudioJob.source_name || 'Generating audio...'}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {currentAudioJob.progress || 'Starting...'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Ad Generation Progress */}
            {isGeneratingAd && currentAdJob && (
              <div className="p-2 bg-primary/5 rounded-md border border-primary/20 overflow-hidden">
                <div className="flex items-center gap-2">
                  <SpinnerGap size={14} className="animate-spin text-primary flex-shrink-0" />
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <p className="text-xs font-medium truncate">
                      {currentAdJob.product_name || 'Generating ads...'}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {currentAdJob.progress || 'Starting...'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Flash Card Generation Progress */}
            {isGeneratingFlashCards && (
              <div className="p-2 bg-purple-500/5 rounded-md border border-purple-500/20 overflow-hidden">
                <div className="flex items-center gap-2">
                  <SpinnerGap size={14} className="animate-spin text-purple-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <p className="text-xs font-medium truncate">
                      {currentFlashCardJob?.source_name || 'Generating flash cards...'}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {currentFlashCardJob?.progress || 'Starting...'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Mind Map Generation Progress */}
            {isGeneratingMindMap && (
              <div className="p-2 bg-blue-500/5 rounded-md border border-blue-500/20 overflow-hidden">
                <div className="flex items-center gap-2">
                  <SpinnerGap size={14} className="animate-spin text-blue-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <p className="text-xs font-medium truncate">
                      {currentMindMapJob?.source_name || 'Generating mind map...'}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {currentMindMapJob?.progress || 'Starting...'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Quiz Generation Progress */}
            {isGeneratingQuiz && (
              <div className="p-2 bg-orange-500/5 rounded-md border border-orange-500/20 overflow-hidden">
                <div className="flex items-center gap-2">
                  <SpinnerGap size={14} className="animate-spin text-orange-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <p className="text-xs font-medium truncate">
                      {currentQuizJob?.source_name || 'Generating quiz...'}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {currentQuizJob?.progress || 'Starting...'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Only show generated content when signals are present (chat selected) */}
            {signals.length > 0 ? (
              <>
                {/* Saved Audio Jobs - filter by source_id from signals */}
                {savedAudioJobs
                  .filter((job) => signals.some((s) =>
                    s.sources.some((src) => src.source_id === job.source_id)
                  ))
                  .map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors"
                    >
                      <div className="p-1 bg-primary/10 rounded flex-shrink-0">
                        <SpeakerHigh size={12} className="text-primary" />
                      </div>
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <p className="text-[10px] font-medium truncate max-w-[120px]">{job.source_name}</p>
                      </div>
                      <div className="flex items-center gap-0.5 flex-shrink-0">
                        <Button
                          size="sm"
                          variant={playingJobId === job.id ? 'default' : 'ghost'}
                          className="h-5 w-5 p-0"
                          onClick={() => playingJobId === job.id ? pauseAudio() : playAudio(job)}
                        >
                          {playingJobId === job.id ? (
                            <Pause size={10} weight="fill" />
                          ) : (
                            <Play size={10} weight="fill" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-5 w-5 p-0"
                          onClick={() => downloadAudio(job)}
                        >
                          <DownloadSimple size={10} />
                        </Button>
                      </div>
                    </div>
                  ))}

                {/* Saved Ad Jobs - show if ads_creative signal exists */}
                {signals.some((s) => s.studio_item === 'ads_creative') &&
                  savedAdJobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
                      onClick={() => setViewingAdJob(job)}
                    >
                      <div className="p-1 bg-green-500/10 rounded flex-shrink-0">
                        <Image size={12} className="text-green-600" />
                      </div>
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <p className="text-[10px] font-medium truncate max-w-[120px]">Ad Creatives</p>
                      </div>
                      <span className="text-[9px] text-muted-foreground flex-shrink-0">
                        {job.images.length}
                      </span>
                    </div>
                  ))}

                {/* Saved Flash Card Jobs - filter by source_id from signals */}
                {savedFlashCardJobs
                  .filter((job) => signals.some((s) =>
                    s.sources.some((src) => src.source_id === job.source_id)
                  ))
                  .map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
                      onClick={() => {
                        setViewingFlashCardJob(job);
                        setCurrentCardIndex(0);
                        setIsCardFlipped(false);
                      }}
                    >
                      <div className="p-1 bg-purple-500/10 rounded flex-shrink-0">
                        <Cards size={12} className="text-purple-600" />
                      </div>
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <p className="text-[10px] font-medium truncate max-w-[120px]">{job.source_name}</p>
                      </div>
                      <span className="text-[9px] text-muted-foreground flex-shrink-0">
                        {job.card_count}
                      </span>
                    </div>
                  ))}

                {/* Saved Mind Map Jobs - filter by source_id from signals */}
                {savedMindMapJobs
                  .filter((job) => signals.some((s) =>
                    s.sources.some((src) => src.source_id === job.source_id)
                  ))
                  .map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
                      onClick={() => setViewingMindMapJob(job)}
                    >
                      <div className="p-1 bg-blue-500/10 rounded flex-shrink-0">
                        <TreeStructure size={12} className="text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <p className="text-[10px] font-medium truncate max-w-[120px]">{job.source_name}</p>
                      </div>
                      <span className="text-[9px] text-muted-foreground flex-shrink-0">
                        {job.node_count}
                      </span>
                    </div>
                  ))}

                {/* Saved Quiz Jobs - filter by source_id from signals */}
                {savedQuizJobs
                  .filter((job) => signals.some((s) =>
                    s.sources.some((src) => src.source_id === job.source_id)
                  ))
                  .map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
                      onClick={() => setViewingQuizJob(job)}
                    >
                      <div className="p-1 bg-orange-500/10 rounded flex-shrink-0">
                        <Exam size={12} className="text-orange-600" />
                      </div>
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <p className="text-[10px] font-medium truncate max-w-[120px]">{job.source_name}</p>
                      </div>
                      <span className="text-[9px] text-muted-foreground flex-shrink-0">
                        {job.question_count}
                      </span>
                    </div>
                  ))}
              </>
            ) : (
              /* Empty State - no chat selected */
              <div className="text-center py-6 text-muted-foreground">
                <MagicWand size={20} className="mx-auto mb-1.5 opacity-50" />
                <p className="text-[10px]">Select a chat to see content</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Signal Picker Dialog */}
      <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedItem && getItemIcon(selectedItem) && (
                <span className="text-primary">
                  {React.createElement(getItemIcon(selectedItem)!, { size: 20 })}
                </span>
              )}
              Generate {selectedItem ? getItemTitle(selectedItem) : ''}
            </DialogTitle>
            <DialogDescription>
              Multiple topics available. Choose which one to generate:
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-2 py-4 max-h-[50vh] overflow-y-auto">
            {selectedSignals.map((signal) => (
              <Button
                key={signal.id}
                variant="outline"
                className="h-auto p-3 justify-start text-left flex flex-col items-start gap-1 w-full min-w-0"
                onClick={() => selectedItem && triggerGeneration(selectedItem, signal)}
              >
                <span className="font-medium text-sm line-clamp-2 w-full">
                  {signal.direction}
                </span>
                <span className="text-xs text-muted-foreground">
                  {signal.sources.length} source{signal.sources.length !== 1 ? 's' : ''}
                </span>
              </Button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Ad Creative Viewer Modal */}
      <Dialog open={viewingAdJob !== null} onOpenChange={(open) => !open && setViewingAdJob(null)}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Image size={20} className="text-green-600" />
              Ad Creatives - {viewingAdJob?.product_name}
            </DialogTitle>
            <DialogDescription>
              {viewingAdJob?.images.length} creative{viewingAdJob?.images.length !== 1 ? 's' : ''} generated for Facebook and Instagram
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-4">
            {viewingAdJob?.images.map((image, index) => (
              <div key={index} className="flex flex-col gap-2">
                <div className="relative group rounded-lg overflow-hidden border bg-muted">
                  <img
                    src={`http://localhost:5000${image.url}`}
                    alt={`${image.type} creative`}
                    className="w-full h-auto object-cover"
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Button
                      size="sm"
                      variant="secondary"
                      className="gap-1"
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = `http://localhost:5000${image.url}`;
                        link.download = image.filename;
                        link.click();
                      }}
                    >
                      <DownloadSimple size={14} />
                      Download
                    </Button>
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-xs font-medium capitalize">{image.type.replace('_', ' ')}</p>
                  <p className="text-[10px] text-muted-foreground line-clamp-2">{image.prompt}</p>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Flash Card Viewer Modal - Carousel Style */}
      <Dialog open={viewingFlashCardJob !== null} onOpenChange={(open) => {
        if (!open) {
          setViewingFlashCardJob(null);
          setCurrentCardIndex(0);
          setIsCardFlipped(false);
        }
      }}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Cards size={20} className="text-purple-600" />
              {viewingFlashCardJob?.source_name}
            </DialogTitle>
            {viewingFlashCardJob?.topic_summary && (
              <DialogDescription>
                {viewingFlashCardJob.topic_summary}
              </DialogDescription>
            )}
          </DialogHeader>

          {/* Flip instruction */}
          <p className="text-xs text-center text-muted-foreground">
            Click card to flip
          </p>

          {/* Card Carousel */}
          <div className="flex items-center justify-center gap-4 py-4">
            {/* Previous Button */}
            <button
              onClick={prevCard}
              disabled={currentCardIndex === 0}
              className={`p-3 rounded-full border transition-all ${
                currentCardIndex === 0
                  ? 'opacity-30 cursor-not-allowed border-muted'
                  : 'hover:bg-muted border-border hover:border-primary/50'
              }`}
            >
              <CaretLeft size={20} className="text-muted-foreground" />
            </button>

            {/* Flash Card with 3D Flip */}
            {viewingFlashCardJob?.cards[currentCardIndex] && (
              <div
                className="relative w-full max-w-md cursor-pointer"
                style={{ perspective: '1000px' }}
                onClick={toggleCardFlip}
              >
                <div
                  className="relative w-full transition-transform duration-500"
                  style={{
                    transformStyle: 'preserve-3d',
                    transform: isCardFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                  }}
                >
                  {/* Front of Card (Question) */}
                  <div
                    className="w-full min-h-[280px] p-6 rounded-2xl bg-zinc-900 dark:bg-zinc-900 text-white flex flex-col"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className="flex-1 flex items-center justify-center">
                      <p className="text-xl font-medium text-center leading-relaxed">
                        {viewingFlashCardJob.cards[currentCardIndex].front}
                      </p>
                    </div>
                    <div className="flex items-center justify-between mt-4">
                      <span className="text-xs text-zinc-400 capitalize">
                        {viewingFlashCardJob.cards[currentCardIndex].category}
                      </span>
                      <span className="text-xs text-zinc-500">
                        Click to see answer
                      </span>
                    </div>
                  </div>

                  {/* Back of Card (Answer) */}
                  <div
                    className="absolute inset-0 w-full min-h-[280px] p-6 rounded-2xl bg-gradient-to-br from-green-600 to-green-700 text-white flex flex-col"
                    style={{
                      backfaceVisibility: 'hidden',
                      transform: 'rotateY(180deg)',
                    }}
                  >
                    <div className="flex-1 flex items-center justify-center">
                      <p className="text-lg text-center leading-relaxed">
                        {viewingFlashCardJob.cards[currentCardIndex].back}
                      </p>
                    </div>
                    <div className="flex items-center justify-between mt-4">
                      <span className="text-xs text-green-200">
                        Answer
                      </span>
                      <span className="text-xs text-green-300">
                        Click to see question
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Next Button */}
            <button
              onClick={nextCard}
              disabled={!viewingFlashCardJob || currentCardIndex >= viewingFlashCardJob.cards.length - 1}
              className={`p-3 rounded-full border transition-all ${
                !viewingFlashCardJob || currentCardIndex >= viewingFlashCardJob.cards.length - 1
                  ? 'opacity-30 cursor-not-allowed border-muted'
                  : 'hover:bg-muted border-border hover:border-primary/50'
              }`}
            >
              <CaretRight size={20} className="text-muted-foreground" />
            </button>
          </div>

          {/* Progress Indicator */}
          <div className="flex items-center justify-center gap-3">
            {/* Reset Button */}
            <button
              onClick={() => {
                setCurrentCardIndex(0);
                setIsCardFlipped(false);
              }}
              className="p-1.5 rounded hover:bg-muted transition-colors"
              title="Reset to first card"
            >
              <ArrowsClockwise size={16} className="text-muted-foreground" />
            </button>

            {/* Progress Bar */}
            <div className="flex-1 max-w-[200px] h-1 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-300"
                style={{
                  width: viewingFlashCardJob
                    ? `${((currentCardIndex + 1) / viewingFlashCardJob.cards.length) * 100}%`
                    : '0%'
                }}
              />
            </div>

            {/* Card Counter */}
            <span className="text-sm text-muted-foreground min-w-[60px] text-right">
              {currentCardIndex + 1} / {viewingFlashCardJob?.card_count || 0} cards
            </span>
          </div>
        </DialogContent>
      </Dialog>

      {/* Mind Map Viewer Modal */}
      <Dialog open={viewingMindMapJob !== null} onOpenChange={(open) => !open && setViewingMindMapJob(null)}>
        <DialogContent className="sm:max-w-5xl h-[85vh] p-0 flex flex-col">
          <DialogHeader className="px-6 py-4 border-b flex-shrink-0">
            <DialogTitle className="flex items-center gap-2">
              <TreeStructure size={20} className="text-blue-600" />
              {viewingMindMapJob?.source_name}
            </DialogTitle>
            {viewingMindMapJob?.topic_summary && (
              <DialogDescription>
                {viewingMindMapJob.topic_summary}
              </DialogDescription>
            )}
          </DialogHeader>

          {/* Mind Map Visualization */}
          <div className="flex-1 min-h-0">
            {viewingMindMapJob && (
              <MindMapViewer
                nodes={viewingMindMapJob.nodes}
                topicSummary={viewingMindMapJob.topic_summary}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Quiz Viewer Modal */}
      <Dialog open={viewingQuizJob !== null} onOpenChange={(open) => !open && setViewingQuizJob(null)}>
        <DialogContent className="sm:max-w-3xl h-[85vh] p-0 flex flex-col">
          <DialogHeader className="px-6 py-4 border-b flex-shrink-0">
            <DialogTitle className="flex items-center gap-2">
              <Exam size={20} className="text-orange-600" />
              Quiz - {viewingQuizJob?.source_name}
            </DialogTitle>
            {viewingQuizJob?.topic_summary && (
              <DialogDescription>
                {viewingQuizJob.topic_summary}
              </DialogDescription>
            )}
          </DialogHeader>

          {/* Quiz Viewer */}
          <div className="flex-1 min-h-0">
            {viewingQuizJob && (
              <QuizViewer
                questions={viewingQuizJob.questions}
                topicSummary={viewingQuizJob.topic_summary}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
