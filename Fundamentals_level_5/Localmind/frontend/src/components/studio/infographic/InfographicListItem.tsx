/**
 * InfographicListItem Component
 * Educational Note: Renders a saved infographic in the Generated Content list.
 */

import React from 'react';
import { ChartPieSlice } from '@phosphor-icons/react';
import type { InfographicJob } from '@/lib/api/studio';

interface InfographicListItemProps {
  job: InfographicJob;
  onClick: () => void;
}

export const InfographicListItem: React.FC<InfographicListItemProps> = ({ job, onClick }) => {
  return (
    <div
      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="p-1 bg-amber-500/10 rounded flex-shrink-0">
        <ChartPieSlice size={12} className="text-amber-600" />
      </div>
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-[10px] font-medium truncate max-w-[120px]">
          {job.topic_title || 'Infographic'}
        </p>
      </div>
    </div>
  );
};
