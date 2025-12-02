/**
 * StudioModals Component
 * Educational Note: Renders all studio viewer modals.
 * Consolidates modal components for cleaner StudioPanel structure.
 */

import React from 'react';
import { AdViewerModal } from './ads';
import { FlashCardViewerModal } from './flashcards';
import { MindMapViewerModal } from './mindmap';
import { QuizViewerModal } from './quiz';
import { SocialPostViewerModal } from './social';
import { InfographicViewerModal } from './infographic';
import { EmailViewerModal } from './email';
import type {
  AdJob,
  FlashCardJob,
  MindMapJob,
  QuizJob,
  SocialPostJob,
  InfographicJob,
  EmailJob
} from '../../lib/api/studio';

interface StudioModalsProps {
  projectId: string;

  // Ads
  viewingAdJob: AdJob | null;
  setViewingAdJob: (job: AdJob | null) => void;

  // Flash Cards
  viewingFlashCardJob: FlashCardJob | null;
  setViewingFlashCardJob: (job: FlashCardJob | null) => void;

  // Mind Map
  viewingMindMapJob: MindMapJob | null;
  setViewingMindMapJob: (job: MindMapJob | null) => void;

  // Quiz
  viewingQuizJob: QuizJob | null;
  setViewingQuizJob: (job: QuizJob | null) => void;

  // Social Posts
  viewingSocialPostJob: SocialPostJob | null;
  setViewingSocialPostJob: (job: SocialPostJob | null) => void;

  // Infographic
  viewingInfographicJob: InfographicJob | null;
  setViewingInfographicJob: (job: InfographicJob | null) => void;

  // Email
  viewingEmailJob: EmailJob | null;
  setViewingEmailJob: (job: EmailJob | null) => void;
}

export const StudioModals: React.FC<StudioModalsProps> = ({
  projectId,
  viewingAdJob,
  setViewingAdJob,
  viewingFlashCardJob,
  setViewingFlashCardJob,
  viewingMindMapJob,
  setViewingMindMapJob,
  viewingQuizJob,
  setViewingQuizJob,
  viewingSocialPostJob,
  setViewingSocialPostJob,
  viewingInfographicJob,
  setViewingInfographicJob,
  viewingEmailJob,
  setViewingEmailJob,
}) => {
  return (
    <>
      {/* Ad Creative Viewer Modal */}
      <AdViewerModal
        viewingAdJob={viewingAdJob}
        onClose={() => setViewingAdJob(null)}
      />

      {/* Flash Card Viewer Modal */}
      <FlashCardViewerModal
        viewingFlashCardJob={viewingFlashCardJob}
        onClose={() => setViewingFlashCardJob(null)}
      />

      {/* Mind Map Viewer Modal */}
      <MindMapViewerModal
        viewingMindMapJob={viewingMindMapJob}
        onClose={() => setViewingMindMapJob(null)}
      />

      {/* Quiz Viewer Modal */}
      <QuizViewerModal
        viewingQuizJob={viewingQuizJob}
        onClose={() => setViewingQuizJob(null)}
      />

      {/* Social Post Viewer Modal */}
      <SocialPostViewerModal
        viewingSocialPostJob={viewingSocialPostJob}
        onClose={() => setViewingSocialPostJob(null)}
      />

      {/* Infographic Viewer Modal */}
      <InfographicViewerModal
        viewingInfographicJob={viewingInfographicJob}
        onClose={() => setViewingInfographicJob(null)}
      />

      {/* Email Template Modal */}
      <EmailViewerModal
        projectId={projectId}
        viewingEmailJob={viewingEmailJob}
        onClose={() => setViewingEmailJob(null)}
      />
    </>
  );
};
