/**
 * StudioProgressIndicators Component
 * Educational Note: Shows progress for all active studio generation jobs.
 * Consolidates all progress indicators in one place.
 */

import React from 'react';
import { AudioProgressIndicator } from './audio';
import { AdProgressIndicator } from './ads';
import { FlashCardProgressIndicator } from './flashcards';
import { MindMapProgressIndicator } from './mindmap';
import { WebsiteProgressIndicator } from './website';
import { QuizProgressIndicator } from './quiz';
import { SocialPostProgressIndicator } from './social';
import { InfographicProgressIndicator } from './infographic';
import { EmailProgressIndicator } from './email';
import { ComponentProgressIndicator } from './components';
import { VideoProgressIndicator } from './video';
import { FlowDiagramProgressIndicator } from './flow-diagrams';
import { WireframeProgressIndicator } from './wireframes';
import { PresentationProgressIndicator } from './presentations';
import { PRDProgressIndicator } from './prd';
import { MarketingStrategyProgressIndicator } from './marketingStrategy';
import { BlogProgressIndicator } from './blog';
import { BusinessReportProgressIndicator } from './businessReport';
import type { AudioJob, AdJob, FlashCardJob, MindMapJob, WebsiteJob, QuizJob, SocialPostJob, InfographicJob, EmailJob, ComponentJob, VideoJob, FlowDiagramJob, WireframeJob, PresentationJob, PRDJob, MarketingStrategyJob, BlogJob, BusinessReportJob } from '@/lib/api/studio';

interface StudioProgressIndicatorsProps {
  // Audio
  isGeneratingAudio: boolean;
  currentAudioJob: AudioJob | null;

  // Ads
  isGeneratingAd: boolean;
  currentAdJob: AdJob | null;

  // Flash Cards
  isGeneratingFlashCards: boolean;
  currentFlashCardJob: FlashCardJob | null;

  // Mind Map
  isGeneratingMindMap: boolean;
  currentMindMapJob: MindMapJob | null;

  // Website
  isGeneratingWebsite: boolean;
  currentWebsiteJob: WebsiteJob | null;

  // Quiz
  isGeneratingQuiz: boolean;
  currentQuizJob: QuizJob | null;

  // Social Posts
  isGeneratingSocialPosts: boolean;
  currentSocialPostJob: SocialPostJob | null;

  // Infographic
  isGeneratingInfographic: boolean;
  currentInfographicJob: InfographicJob | null;

  // Email
  isGeneratingEmail: boolean;
  currentEmailJob: EmailJob | null;

  // Components
  isGeneratingComponents: boolean;
  currentComponentJob: ComponentJob | null;

  // Video
  isGeneratingVideo: boolean;
  currentVideoJob: VideoJob | null;

  // Flow Diagram
  isGeneratingFlowDiagram: boolean;
  currentFlowDiagramJob: FlowDiagramJob | null;

  // Wireframe
  isGeneratingWireframe: boolean;
  currentWireframeJob: WireframeJob | null;

  // Presentation
  isGeneratingPresentation: boolean;
  currentPresentationJob: PresentationJob | null;

  // PRD
  isGeneratingPRD: boolean;
  currentPRDJob: PRDJob | null;

  // Marketing Strategy
  isGeneratingMarketingStrategy: boolean;
  currentMarketingStrategyJob: MarketingStrategyJob | null;

  // Blog
  isGeneratingBlog: boolean;
  currentBlogJob: BlogJob | null;

  // Business Report
  isGeneratingBusinessReport: boolean;
  currentBusinessReportJob: BusinessReportJob | null;
}

export const StudioProgressIndicators: React.FC<StudioProgressIndicatorsProps> = ({
  isGeneratingAudio,
  currentAudioJob,
  isGeneratingAd,
  currentAdJob,
  isGeneratingFlashCards,
  currentFlashCardJob,
  isGeneratingMindMap,
  currentMindMapJob,
  isGeneratingWebsite,
  currentWebsiteJob,
  isGeneratingQuiz,
  currentQuizJob,
  isGeneratingSocialPosts,
  currentSocialPostJob,
  isGeneratingInfographic,
  currentInfographicJob,
  isGeneratingEmail,
  currentEmailJob,
  isGeneratingComponents,
  currentComponentJob,
  isGeneratingVideo,
  currentVideoJob,
  isGeneratingFlowDiagram,
  currentFlowDiagramJob,
  isGeneratingWireframe,
  currentWireframeJob,
  isGeneratingPresentation,
  currentPresentationJob,
  isGeneratingPRD,
  currentPRDJob,
  isGeneratingMarketingStrategy,
  currentMarketingStrategyJob,
  isGeneratingBlog,
  currentBlogJob,
  isGeneratingBusinessReport,
  currentBusinessReportJob,
}) => {
  return (
    <>
      {/* Audio Generation Progress */}
      {isGeneratingAudio && (
        <AudioProgressIndicator currentAudioJob={currentAudioJob} />
      )}

      {/* Ad Generation Progress */}
      {isGeneratingAd && (
        <AdProgressIndicator currentAdJob={currentAdJob} />
      )}

      {/* Flash Card Generation Progress */}
      {isGeneratingFlashCards && (
        <FlashCardProgressIndicator currentFlashCardJob={currentFlashCardJob} />
      )}

      {/* Mind Map Generation Progress */}
      {isGeneratingMindMap && (
        <MindMapProgressIndicator currentMindMapJob={currentMindMapJob} />
      )}

      {/* Website Generation Progress */}
      {isGeneratingWebsite && (
        <WebsiteProgressIndicator currentWebsiteJob={currentWebsiteJob} />
      )}

      {/* Quiz Generation Progress */}
      {isGeneratingQuiz && (
        <QuizProgressIndicator currentQuizJob={currentQuizJob} />
      )}

      {/* Social Post Generation Progress */}
      {isGeneratingSocialPosts && (
        <SocialPostProgressIndicator currentSocialPostJob={currentSocialPostJob} />
      )}

      {/* Infographic Generation Progress */}
      {isGeneratingInfographic && (
        <InfographicProgressIndicator currentInfographicJob={currentInfographicJob} />
      )}

      {/* Email Template Generation Progress */}
      {isGeneratingEmail && (
        <EmailProgressIndicator currentEmailJob={currentEmailJob} />
      )}

      {/* Component Generation Progress */}
      {isGeneratingComponents && (
        <ComponentProgressIndicator currentComponentJob={currentComponentJob} />
      )}

      {/* Video Generation Progress */}
      {isGeneratingVideo && (
        <VideoProgressIndicator currentVideoJob={currentVideoJob} />
      )}

      {/* Flow Diagram Generation Progress */}
      {isGeneratingFlowDiagram && (
        <FlowDiagramProgressIndicator currentFlowDiagramJob={currentFlowDiagramJob} />
      )}

      {/* Wireframe Generation Progress */}
      {isGeneratingWireframe && (
        <WireframeProgressIndicator currentWireframeJob={currentWireframeJob} />
      )}

      {/* Presentation Generation Progress */}
      {isGeneratingPresentation && (
        <PresentationProgressIndicator currentPresentationJob={currentPresentationJob} />
      )}

      {/* PRD Generation Progress */}
      {isGeneratingPRD && (
        <PRDProgressIndicator currentPRDJob={currentPRDJob} />
      )}

      {/* Marketing Strategy Generation Progress */}
      {isGeneratingMarketingStrategy && (
        <MarketingStrategyProgressIndicator currentMarketingStrategyJob={currentMarketingStrategyJob} />
      )}

      {/* Blog Generation Progress */}
      {isGeneratingBlog && (
        <BlogProgressIndicator currentBlogJob={currentBlogJob} />
      )}

      {/* Business Report Generation Progress */}
      {isGeneratingBusinessReport && (
        <BusinessReportProgressIndicator currentBusinessReportJob={currentBusinessReportJob} />
      )}
    </>
  );
};
