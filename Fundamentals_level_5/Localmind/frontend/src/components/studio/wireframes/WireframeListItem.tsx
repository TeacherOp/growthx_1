/**
 * WireframeListItem Component
 * Educational Note: Renders a saved wireframe in the Generated Content list.
 * Clicking opens the wireframe in the Excalidraw viewer modal.
 */

import React from 'react';
import { Browser } from '@phosphor-icons/react';
import type { WireframeJob } from '@/lib/api/studio/wireframes';

interface WireframeListItemProps {
  job: WireframeJob;
  onClick: () => void;
}

export const WireframeListItem: React.FC<WireframeListItemProps> = ({ job, onClick }) => {
  return (
    <div
      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="p-1 bg-purple-500/10 rounded flex-shrink-0">
        <Browser size={12} className="text-purple-600" />
      </div>
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-[10px] font-medium truncate max-w-[120px]">
          {job.title || 'Wireframe'}
        </p>
        <p className="text-[9px] text-muted-foreground truncate">
          {job.element_count} elements
        </p>
      </div>
    </div>
  );
};
