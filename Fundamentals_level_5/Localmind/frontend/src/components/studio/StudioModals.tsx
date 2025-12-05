/**
 * StudioModals Component
 * Educational Note: Renders all studio viewer modals.
 * Consolidates modal components for cleaner StudioPanel structure.
 */

import React from 'react';
import { AdViewerModal } from './ads';
import { FlashCardViewerModal } from './flashcards';
import { MindMapViewerModal } from './mindmap';
import { WebsiteViewerModal } from './website';
import { QuizViewerModal } from './quiz';
import { SocialPostViewerModal } from './social';
import { InfographicViewerModal } from './infographic';
import { EmailViewerModal } from './email';
import { ComponentViewerModal } from './components';
import { VideoViewerModal } from './video';
import { FlowDiagramViewerModal } from './flow-diagrams';
import { WireframeViewerModal } from './wireframes';
import { PresentationViewerModal } from './presentations';
import { PRDViewerModal } from './prd';
import { MarketingStrategyViewerModal } from './marketingStrategy';
import { BlogViewerModal } from './blog';
import { BusinessReportViewerModal } from './businessReport';
import type {
  AdJob,
  FlashCardJob,
  MindMapJob,
  WebsiteJob,
  QuizJob,
  SocialPostJob,
  InfographicJob,
  EmailJob,
  ComponentJob,
  VideoJob,
  FlowDiagramJob,
  WireframeJob,
  PresentationJob,
  PRDJob,
  MarketingStrategyJob,
  BlogJob,
  BusinessReportJob
} from '@/lib/api/studio';

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

  // Website
  viewingWebsiteJob: WebsiteJob | null;
  setViewingWebsiteJob: (job: WebsiteJob | null) => void;

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

  // Components
  viewingComponentJob: ComponentJob | null;
  setViewingComponentJob: (job: ComponentJob | null) => void;

  // Video
  viewingVideoJob: VideoJob | null;
  setViewingVideoJob: (job: VideoJob | null) => void;
  downloadVideo: (jobId: string, filename: string) => void;

  // Flow Diagram
  viewingFlowDiagramJob: FlowDiagramJob | null;
  setViewingFlowDiagramJob: (job: FlowDiagramJob | null) => void;

  // Wireframe
  viewingWireframeJob: WireframeJob | null;
  setViewingWireframeJob: (job: WireframeJob | null) => void;

  // Presentation
  viewingPresentationJob: PresentationJob | null;
  setViewingPresentationJob: (job: PresentationJob | null) => void;
  downloadPresentation: (jobId: string) => void;

  // PRD
  viewingPRDJob: PRDJob | null;
  setViewingPRDJob: (job: PRDJob | null) => void;
  downloadPRD: (jobId: string) => void;

  // Marketing Strategy
  viewingMarketingStrategyJob: MarketingStrategyJob | null;
  setViewingMarketingStrategyJob: (job: MarketingStrategyJob | null) => void;
  downloadMarketingStrategy: (jobId: string) => void;

  // Blog
  viewingBlogJob: BlogJob | null;
  setViewingBlogJob: (job: BlogJob | null) => void;
  downloadBlog: (jobId: string) => void;

  // Business Report
  viewingBusinessReportJob: BusinessReportJob | null;
  setViewingBusinessReportJob: (job: BusinessReportJob | null) => void;
  downloadBusinessReport: (jobId: string) => void;
}

export const StudioModals: React.FC<StudioModalsProps> = ({
  projectId,
  viewingAdJob,
  setViewingAdJob,
  viewingFlashCardJob,
  setViewingFlashCardJob,
  viewingMindMapJob,
  setViewingMindMapJob,
  viewingWebsiteJob,
  setViewingWebsiteJob,
  viewingQuizJob,
  setViewingQuizJob,
  viewingSocialPostJob,
  setViewingSocialPostJob,
  viewingInfographicJob,
  setViewingInfographicJob,
  viewingEmailJob,
  setViewingEmailJob,
  viewingComponentJob,
  setViewingComponentJob,
  viewingVideoJob,
  setViewingVideoJob,
  downloadVideo,
  viewingFlowDiagramJob,
  setViewingFlowDiagramJob,
  viewingWireframeJob,
  setViewingWireframeJob,
  viewingPresentationJob,
  setViewingPresentationJob,
  downloadPresentation,
  viewingPRDJob,
  setViewingPRDJob,
  downloadPRD,
  viewingMarketingStrategyJob,
  setViewingMarketingStrategyJob,
  downloadMarketingStrategy,
  viewingBlogJob,
  setViewingBlogJob,
  downloadBlog,
  viewingBusinessReportJob,
  setViewingBusinessReportJob,
  downloadBusinessReport,
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

      {/* Website Viewer Modal */}
      <WebsiteViewerModal
        projectId={projectId}
        viewingWebsiteJob={viewingWebsiteJob}
        onClose={() => setViewingWebsiteJob(null)}
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

      {/* Component Viewer Modal */}
      <ComponentViewerModal
        projectId={projectId}
        viewingComponentJob={viewingComponentJob}
        onClose={() => setViewingComponentJob(null)}
      />

      {/* Video Viewer Modal */}
      <VideoViewerModal
        projectId={projectId}
        viewingVideoJob={viewingVideoJob}
        onClose={() => setViewingVideoJob(null)}
        onDownload={(filename) => {
          if (viewingVideoJob) {
            downloadVideo(viewingVideoJob.id, filename);
          }
        }}
      />

      {/* Flow Diagram Viewer Modal */}
      <FlowDiagramViewerModal
        job={viewingFlowDiagramJob}
        onClose={() => setViewingFlowDiagramJob(null)}
      />

      {/* Wireframe Viewer Modal */}
      <WireframeViewerModal
        job={viewingWireframeJob}
        onClose={() => setViewingWireframeJob(null)}
      />

      {/* Presentation Viewer Modal */}
      <PresentationViewerModal
        projectId={projectId}
        viewingPresentationJob={viewingPresentationJob}
        onClose={() => setViewingPresentationJob(null)}
        onDownloadPptx={downloadPresentation}
      />

      {/* PRD Viewer Modal */}
      <PRDViewerModal
        projectId={projectId}
        viewingPRDJob={viewingPRDJob}
        onClose={() => setViewingPRDJob(null)}
        onDownload={downloadPRD}
      />

      {/* Marketing Strategy Viewer Modal */}
      <MarketingStrategyViewerModal
        projectId={projectId}
        viewingMarketingStrategyJob={viewingMarketingStrategyJob}
        onClose={() => setViewingMarketingStrategyJob(null)}
        onDownload={downloadMarketingStrategy}
      />

      {/* Blog Viewer Modal */}
      <BlogViewerModal
        projectId={projectId}
        viewingBlogJob={viewingBlogJob}
        onClose={() => setViewingBlogJob(null)}
        onDownload={downloadBlog}
      />

      {/* Business Report Viewer Modal */}
      <BusinessReportViewerModal
        projectId={projectId}
        viewingBusinessReportJob={viewingBusinessReportJob}
        onClose={() => setViewingBusinessReportJob(null)}
        onDownload={downloadBusinessReport}
      />
    </>
  );
};
