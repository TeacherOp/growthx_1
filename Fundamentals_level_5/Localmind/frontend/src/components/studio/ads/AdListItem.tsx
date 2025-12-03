/**
 * AdListItem Component
 * Educational Note: Renders saved ad creatives in the Generated Content list.
 */

import React from 'react';
import { Image } from '@phosphor-icons/react';
import type { AdJob } from '@/lib/api/studio';

interface AdListItemProps {
  job: AdJob;
  onClick: () => void;
}

export const AdListItem: React.FC<AdListItemProps> = ({ job, onClick }) => {
  return (
    <div
      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="p-1 bg-green-500/10 rounded flex-shrink-0">
        <Image size={12} className="text-green-600" />
      </div>
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-[10px] font-medium truncate max-w-[120px]">Ad Creatives</p>
      </div>
      <span className="text-[9px] text-muted-foreground flex-shrink-0">
        {job.images.length}
      </span>
    </div>
  );
};
