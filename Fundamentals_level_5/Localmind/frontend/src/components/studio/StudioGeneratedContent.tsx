/**
 * StudioGeneratedContent Component
 * Educational Note: Displays all generated studio content items.
 * Shows list items for each completed job, filtered by active signals.
 */

import React from 'react';
import { MagicWand } from '@phosphor-icons/react';
import { AudioListItem } from './audio';
import { AdListItem } from './ads';
import { FlashCardListItem } from './flashcards';
import { MindMapListItem } from './mindmap';
import { WebsiteListItem } from './website';
import { QuizListItem } from './quiz';
import { SocialPostListItem } from './social';
import { InfographicListItem } from './infographic';
import { EmailListItem } from './email';
import type {
  AudioJob,
  AdJob,
  FlashCardJob,
  MindMapJob,
  WebsiteJob,
  QuizJob,
  SocialPostJob,
  InfographicJob,
  EmailJob
} from '../../lib/api/studio';
import type { StudioSignal } from './types';

interface StudioGeneratedContentProps {
  signals: StudioSignal[];

  // Audio
  savedAudioJobs: AudioJob[];
  playingJobId: string | null;
  playAudio: (job: AudioJob) => void;
  pauseAudio: () => void;
  downloadAudio: (job: AudioJob) => void;

  // Ads
  savedAdJobs: AdJob[];
  setViewingAdJob: (job: AdJob) => void;

  // Flash Cards
  savedFlashCardJobs: FlashCardJob[];
  setViewingFlashCardJob: (job: FlashCardJob) => void;

  // Mind Map
  savedMindMapJobs: MindMapJob[];
  setViewingMindMapJob: (job: MindMapJob) => void;

  // Website
  savedWebsiteJobs: WebsiteJob[];
  openWebsite: (jobId: string) => void;
  downloadWebsite: (jobId: string) => void;

  // Quiz
  savedQuizJobs: QuizJob[];
  setViewingQuizJob: (job: QuizJob) => void;

  // Social Posts
  savedSocialPostJobs: SocialPostJob[];
  setViewingSocialPostJob: (job: SocialPostJob) => void;

  // Infographic
  savedInfographicJobs: InfographicJob[];
  setViewingInfographicJob: (job: InfographicJob) => void;

  // Email
  savedEmailJobs: EmailJob[];
  setViewingEmailJob: (job: EmailJob) => void;
}

export const StudioGeneratedContent: React.FC<StudioGeneratedContentProps> = ({
  signals,
  savedAudioJobs,
  playingJobId,
  playAudio,
  pauseAudio,
  downloadAudio,
  savedAdJobs,
  setViewingAdJob,
  savedFlashCardJobs,
  setViewingFlashCardJob,
  savedMindMapJobs,
  setViewingMindMapJob,
  savedWebsiteJobs,
  openWebsite,
  downloadWebsite,
  savedQuizJobs,
  setViewingQuizJob,
  savedSocialPostJobs,
  setViewingSocialPostJob,
  savedInfographicJobs,
  setViewingInfographicJob,
  savedEmailJobs,
  setViewingEmailJob,
}) => {
  if (signals.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        <MagicWand size={20} className="mx-auto mb-1.5 opacity-50" />
        <p className="text-[10px]">Select a chat to see content</p>
      </div>
    );
  }

  return (
    <>
      {/* Saved Audio Jobs - filter by source_id from signals */}
      {savedAudioJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <AudioListItem
            key={job.id}
            job={job}
            playingJobId={playingJobId}
            onPlay={playAudio}
            onPause={pauseAudio}
            onDownload={downloadAudio}
          />
        ))}

      {/* Saved Ad Jobs - show if ads_creative signal exists */}
      {signals.some((s) => s.studio_item === 'ads_creative') &&
        savedAdJobs.map((job) => (
          <AdListItem
            key={job.id}
            job={job}
            onClick={() => setViewingAdJob(job)}
          />
        ))}

      {/* Saved Flash Card Jobs - filter by source_id from signals */}
      {savedFlashCardJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <FlashCardListItem
            key={job.id}
            job={job}
            onClick={() => setViewingFlashCardJob(job)}
          />
        ))}

      {/* Saved Mind Map Jobs - filter by source_id from signals */}
      {savedMindMapJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <MindMapListItem
            key={job.id}
            job={job}
            onClick={() => setViewingMindMapJob(job)}
          />
        ))}

      {/* Saved Website Jobs - filter by source_id from signals */}
      {savedWebsiteJobs
        .filter((job) =>
          signals.some((s) => s.sources.some((src) => src.source_id === job.source_id))
        )
        .map((job) => (
          <WebsiteListItem
            key={job.id}
            job={job}
            onOpen={() => openWebsite(job.id)}
            onDownload={(e) => {
              e.stopPropagation();
              downloadWebsite(job.id);
            }}
          />
        ))}

      {/* Saved Quiz Jobs - filter by source_id from signals */}
      {savedQuizJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <QuizListItem
            key={job.id}
            job={job}
            onClick={() => setViewingQuizJob(job)}
          />
        ))}

      {/* Saved Social Post Jobs - show if social signal exists */}
      {signals.some((s) => s.studio_item === 'social') &&
        savedSocialPostJobs.map((job) => (
          <SocialPostListItem
            key={job.id}
            job={job}
            onClick={() => setViewingSocialPostJob(job)}
          />
        ))}

      {/* Saved Infographic Jobs - filter by source_id from signals */}
      {savedInfographicJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <InfographicListItem
            key={job.id}
            job={job}
            onClick={() => setViewingInfographicJob(job)}
          />
        ))}

      {/* Saved Email Template Jobs - filter by source_id from signals */}
      {savedEmailJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <EmailListItem
            key={job.id}
            job={job}
            onClick={() => setViewingEmailJob(job)}
          />
        ))}
    </>
  );
};
