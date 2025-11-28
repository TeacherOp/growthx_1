/**
 * StudioPanel Component
 * Educational Note: Main orchestrator for the Studio panel.
 * Composes header and tools list into a cohesive panel.
 */

import React from 'react';
import { StudioHeader } from './StudioHeader';
import { StudioToolsList } from './StudioToolsList';
import { generationOptions } from './types';
import { ScrollArea } from '../ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import { MagicWand, CaretLeft } from '@phosphor-icons/react';

interface StudioPanelProps {
  projectId: string;
  isCollapsed?: boolean;
  onExpand?: () => void;
}

export const StudioPanel: React.FC<StudioPanelProps> = ({ projectId, isCollapsed, onExpand }) => {
  /**
   * Handle generation request
   * Educational Note: This will be expanded to trigger actual generation workflows.
   */
  const handleGenerate = (optionId: string) => {
    console.log(`Generating ${optionId} for project ${projectId}`);
    // TODO: Implement generation workflows
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

          {/* Action icons */}
          <ScrollArea className="flex-1 w-full">
            <div className="flex flex-col items-center gap-1 px-1">
              {generationOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <Tooltip key={option.id}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleGenerate(option.id)}
                        className="p-2 rounded-lg hover:bg-muted transition-colors w-full flex justify-center"
                      >
                        <IconComponent size={18} className="text-muted-foreground" />
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
      <StudioToolsList onGenerate={handleGenerate} />
    </div>
  );
};
