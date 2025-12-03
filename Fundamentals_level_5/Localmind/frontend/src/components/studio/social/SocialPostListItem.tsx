/**
 * SocialPostListItem Component
 * Educational Note: Renders saved social posts in the Generated Content list.
 */

import React from 'react';
import { ShareNetwork } from '@phosphor-icons/react';
import type { SocialPostJob } from '@/lib/api/studio';

interface SocialPostListItemProps {
  job: SocialPostJob;
  onClick: () => void;
}

export const SocialPostListItem: React.FC<SocialPostListItemProps> = ({ job, onClick }) => {
  return (
    <div
      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="p-1 bg-cyan-500/10 rounded flex-shrink-0">
        <ShareNetwork size={12} className="text-cyan-600" />
      </div>
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-[10px] font-medium truncate max-w-[120px]">Social Posts</p>
      </div>
      <span className="text-[9px] text-muted-foreground flex-shrink-0">
        {job.post_count}
      </span>
    </div>
  );
};
