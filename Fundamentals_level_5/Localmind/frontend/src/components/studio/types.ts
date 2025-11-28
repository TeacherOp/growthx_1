/**
 * Studio Types
 * Educational Note: Centralized type definitions and data for Studio panel.
 */

import {
  FileText,
  Envelope,
  Users,
  ListChecks,
  Brain,
  PresentationChart,
  Headphones,
  Video,
} from '@phosphor-icons/react';

/**
 * Generation option category types
 */
export type GenerationCategory = 'documents' | 'communication' | 'media' | 'analysis';

/**
 * Single generation option configuration
 */
export interface GenerationOption {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  category: GenerationCategory;
}

/**
 * All available generation options
 * Educational Note: Centralized here for easy modification and reuse.
 */
export const generationOptions: GenerationOption[] = [
  // Documents
  {
    id: 'presentation',
    title: 'Generate Presentation',
    description: 'Create slides from your sources',
    icon: PresentationChart,
    category: 'documents',
  },
  {
    id: 'prd',
    title: 'Generate PRD / Docs',
    description: 'Product requirements document',
    icon: FileText,
    category: 'documents',
  },
  {
    id: 'todo',
    title: 'Generate To-Do List',
    description: 'Action items from your content',
    icon: ListChecks,
    category: 'documents',
  },
  // Communication
  {
    id: 'team-email',
    title: 'Draft Team Email',
    description: 'Internal communication draft',
    icon: Envelope,
    category: 'communication',
  },
  {
    id: 'stakeholder-email',
    title: 'Draft Stakeholder Email',
    description: 'External communication draft',
    icon: Users,
    category: 'communication',
  },
  // Media
  {
    id: 'audio-overview',
    title: 'Audio Overview',
    description: 'Podcast-style summary',
    icon: Headphones,
    category: 'media',
  },
  {
    id: 'video-overview',
    title: 'Video Overview',
    description: 'Visual presentation of content',
    icon: Video,
    category: 'media',
  },
  // Analysis
  {
    id: 'mindmap',
    title: 'Generate Mind Map',
    description: 'Visual knowledge structure',
    icon: Brain,
    category: 'analysis',
  },
];

/**
 * Category metadata for section headers
 */
export const categoryMeta: Record<GenerationCategory, { label: string; icon: React.ComponentType<{ size?: number; className?: string }> }> = {
  documents: { label: 'Documents', icon: FileText },
  communication: { label: 'Communication', icon: Envelope },
  media: { label: 'Media', icon: Video },
  analysis: { label: 'Analysis', icon: Brain },
};
