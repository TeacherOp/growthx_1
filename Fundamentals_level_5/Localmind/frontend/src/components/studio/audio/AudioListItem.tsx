/**
 * AudioListItem Component
 * Educational Note: Renders saved audio with inline playback controls.
 * Unique feature: Play/pause/download controls directly in list item.
 */

import React from 'react';
import { SpeakerHigh, Play, Pause, DownloadSimple } from '@phosphor-icons/react';
import { Button } from '../../ui/button';
import type { AudioJob } from '@/lib/api/studio';

interface AudioListItemProps {
  job: AudioJob;
  playingJobId: string | null;
  onPlay: (job: AudioJob) => void;
  onPause: () => void;
  onDownload: (job: AudioJob) => void;
}

export const AudioListItem: React.FC<AudioListItemProps> = ({
  job,
  playingJobId,
  onPlay,
  onPause,
  onDownload,
}) => {
  return (
    <div className="flex items-center gap-2 p-1.5 bg-muted/50 rounded border hover:border-primary/50 transition-colors">
      <div className="p-1 bg-primary/10 rounded flex-shrink-0">
        <SpeakerHigh size={12} className="text-primary" />
      </div>
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-[10px] font-medium truncate max-w-[120px]">{job.source_name}</p>
      </div>
      <div className="flex items-center gap-0.5 flex-shrink-0">
        <Button
          size="sm"
          variant={playingJobId === job.id ? 'default' : 'ghost'}
          className="h-5 w-5 p-0"
          onClick={() => playingJobId === job.id ? onPause() : onPlay(job)}
        >
          {playingJobId === job.id ? (
            <Pause size={10} weight="fill" />
          ) : (
            <Play size={10} weight="fill" />
          )}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-5 w-5 p-0"
          onClick={() => onDownload(job)}
        >
          <DownloadSimple size={10} />
        </Button>
      </div>
    </div>
  );
};
