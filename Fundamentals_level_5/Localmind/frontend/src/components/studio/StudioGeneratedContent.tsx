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
import { ComponentListItem } from './components';
import { VideoListItem } from './video';
import { FlowDiagramListItem } from './flow-diagrams';
import { WireframeListItem } from './wireframes';
import { PresentationListItem } from './presentations';
import { PRDListItem } from './prd';
import { MarketingStrategyListItem } from './marketingStrategy';
import { BlogListItem } from './blog';
import { BusinessReportListItem } from './businessReport';
import type {
  AudioJob,
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
  setViewingWebsiteJob: (job: WebsiteJob) => void;
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

  // Components
  savedComponentJobs: ComponentJob[];
  setViewingComponentJob: (job: ComponentJob) => void;

  // Video
  savedVideoJobs: VideoJob[];
  setViewingVideoJob: (job: VideoJob) => void;
  downloadVideo: (jobId: string, filename: string) => void;

  // Flow Diagram
  savedFlowDiagramJobs: FlowDiagramJob[];
  setViewingFlowDiagramJob: (job: FlowDiagramJob) => void;

  // Wireframe
  savedWireframeJobs: WireframeJob[];
  setViewingWireframeJob: (job: WireframeJob) => void;

  // Presentation
  savedPresentationJobs: PresentationJob[];
  setViewingPresentationJob: (job: PresentationJob) => void;
  downloadPresentation: (jobId: string) => void;

  // PRD
  savedPRDJobs: PRDJob[];
  setViewingPRDJob: (job: PRDJob) => void;
  downloadPRD: (jobId: string) => void;

  // Marketing Strategy
  savedMarketingStrategyJobs: MarketingStrategyJob[];
  setViewingMarketingStrategyJob: (job: MarketingStrategyJob) => void;
  downloadMarketingStrategy: (jobId: string) => void;

  // Blog
  savedBlogJobs: BlogJob[];
  setViewingBlogJob: (job: BlogJob) => void;
  downloadBlog: (jobId: string) => void;

  // Business Report
  savedBusinessReportJobs: BusinessReportJob[];
  setViewingBusinessReportJob: (job: BusinessReportJob) => void;
  downloadBusinessReport: (jobId: string) => void;
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
  setViewingWebsiteJob,
  downloadWebsite,
  savedQuizJobs,
  setViewingQuizJob,
  savedSocialPostJobs,
  setViewingSocialPostJob,
  savedInfographicJobs,
  setViewingInfographicJob,
  savedEmailJobs,
  setViewingEmailJob,
  savedComponentJobs,
  setViewingComponentJob,
  savedVideoJobs,
  setViewingVideoJob,
  downloadVideo,
  savedFlowDiagramJobs,
  setViewingFlowDiagramJob,
  savedWireframeJobs,
  setViewingWireframeJob,
  savedPresentationJobs,
  setViewingPresentationJob,
  downloadPresentation,
  savedPRDJobs,
  setViewingPRDJob,
  downloadPRD,
  savedMarketingStrategyJobs,
  setViewingMarketingStrategyJob,
  downloadMarketingStrategy,
  savedBlogJobs,
  setViewingBlogJob,
  downloadBlog,
  savedBusinessReportJobs,
  setViewingBusinessReportJob,
  downloadBusinessReport,
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
            onOpen={() => setViewingWebsiteJob(job)}
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

      {/* Saved Component Jobs - filter by source_id from signals */}
      {savedComponentJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <ComponentListItem
            key={job.id}
            job={job}
            onClick={() => setViewingComponentJob(job)}
          />
        ))}

      {/* Saved Video Jobs - filter by source_id from signals */}
      {savedVideoJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <VideoListItem
            key={job.id}
            job={job}
            onOpen={() => setViewingVideoJob(job)}
            onDownload={(e) => {
              e.stopPropagation();
              // Download first video by default
              if (job.videos.length > 0) {
                downloadVideo(job.id, job.videos[0].filename);
              }
            }}
          />
        ))}

      {/* Saved Flow Diagram Jobs - filter by source_id from signals */}
      {savedFlowDiagramJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <FlowDiagramListItem
            key={job.id}
            job={job}
            onClick={() => setViewingFlowDiagramJob(job)}
          />
        ))}

      {/* Saved Wireframe Jobs - filter by source_id from signals */}
      {savedWireframeJobs
        .filter((job) => signals.some((s) =>
          s.sources.some((src) => src.source_id === job.source_id)
        ))
        .map((job) => (
          <WireframeListItem
            key={job.id}
            job={job}
            onClick={() => setViewingWireframeJob(job)}
          />
        ))}

      {/* Saved Presentation Jobs - filter by source_id from signals */}
      {savedPresentationJobs
        .filter((job) =>
          signals.some((s) => s.sources.some((src) => src.source_id === job.source_id))
        )
        .map((job) => (
          <PresentationListItem
            key={job.id}
            job={job}
            onOpen={() => setViewingPresentationJob(job)}
            onDownload={(e) => {
              e.stopPropagation();
              downloadPresentation(job.id);
            }}
          />
        ))}

      {/* Saved PRD Jobs - filter by source_id from signals */}
      {savedPRDJobs
        .filter((job) =>
          signals.some((s) => s.sources.some((src) => src.source_id === job.source_id))
        )
        .map((job) => (
          <PRDListItem
            key={job.id}
            job={job}
            onOpen={() => setViewingPRDJob(job)}
            onDownload={(e) => {
              e.stopPropagation();
              downloadPRD(job.id);
            }}
          />
        ))}

      {/* Saved Marketing Strategy Jobs - filter by source_id from signals */}
      {savedMarketingStrategyJobs
        .filter((job) =>
          signals.some((s) => s.sources.some((src) => src.source_id === job.source_id))
        )
        .map((job) => (
          <MarketingStrategyListItem
            key={job.id}
            job={job}
            onOpen={() => setViewingMarketingStrategyJob(job)}
            onDownload={(e) => {
              e.stopPropagation();
              downloadMarketingStrategy(job.id);
            }}
          />
        ))}

      {/* Saved Blog Jobs - filter by source_id from signals */}
      {savedBlogJobs
        .filter((job) =>
          signals.some((s) => s.sources.some((src) => src.source_id === job.source_id))
        )
        .map((job) => (
          <BlogListItem
            key={job.id}
            job={job}
            onOpen={() => setViewingBlogJob(job)}
            onDownload={(e) => {
              e.stopPropagation();
              downloadBlog(job.id);
            }}
          />
        ))}

      {/* Saved Business Report Jobs - filter by source_id from signals */}
      {savedBusinessReportJobs
        .filter((job) =>
          signals.some((s) => s.sources.some((src) => src.source_id === job.source_id))
        )
        .map((job) => (
          <BusinessReportListItem
            key={job.id}
            job={job}
            onOpen={() => setViewingBusinessReportJob(job)}
            onDownload={(e) => {
              e.stopPropagation();
              downloadBusinessReport(job.id);
            }}
          />
        ))}
    </>
  );
};
