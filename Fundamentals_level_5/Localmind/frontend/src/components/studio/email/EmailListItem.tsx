/**
 * EmailListItem Component
 * Educational Note: Renders a saved email template in the Generated Content list.
 */

import React from 'react';
import { ShareNetwork } from '@phosphor-icons/react';
import type { EmailJob } from '@/lib/api/studio';

interface EmailListItemProps {
  job: EmailJob;
  onClick: () => void;
}

export const EmailListItem: React.FC<EmailListItemProps> = ({ job, onClick }) => {
  return (
    <div
      className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="p-1 bg-blue-500/10 rounded flex-shrink-0">
        <ShareNetwork size={12} className="text-blue-600" />
      </div>
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-[10px] font-medium truncate max-w-[120px]">
          {job.template_name || 'Email Template'}
        </p>
      </div>
    </div>
  );
};
