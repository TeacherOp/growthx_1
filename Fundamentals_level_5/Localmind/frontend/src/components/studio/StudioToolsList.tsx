/**
 * StudioToolsList Component
 * Educational Note: Renders all studio tools organized by category.
 */

import React from 'react';
import { ScrollArea } from '../ui/scroll-area';
import { StudioToolItem } from './StudioToolItem';
import { generationOptions, categoryMeta, type GenerationCategory } from './types';

interface StudioToolsListProps {
  onGenerate: (optionId: string) => void;
}

export const StudioToolsList: React.FC<StudioToolsListProps> = ({ onGenerate }) => {
  /**
   * Render tools for a specific category as a grid
   */
  const renderCategoryTools = (category: GenerationCategory) => {
    const options = generationOptions.filter(opt => opt.category === category);
    return (
      <div className="flex flex-col gap-2">
        {options.map((option) => (
          <StudioToolItem key={option.id} option={option} onClick={onGenerate} />
        ))}
      </div>
    );
  };

  /**
   * Render a category section with header and tools
   */
  const renderCategorySection = (category: GenerationCategory) => {
    const meta = categoryMeta[category];
    const Icon = meta.icon;

    return (
      <div key={category}>
        <div className="flex items-center gap-2 mb-2">
          <Icon size={14} className="text-muted-foreground" />
          <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {meta.label}
          </h3>
        </div>
        {renderCategoryTools(category)}
      </div>
    );
  };

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-4">
        {renderCategorySection('documents')}
        {renderCategorySection('communication')}
        {renderCategorySection('media')}
        {renderCategorySection('analysis')}
      </div>
    </ScrollArea>
  );
};
