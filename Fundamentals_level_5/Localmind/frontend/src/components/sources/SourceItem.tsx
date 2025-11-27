/**
 * SourceItem Component
 * Educational Note: Displays a single source with icon, name, size, and action menu.
 * Shows processing status with loading indicator for sources being processed.
 * Shows error indicator for sources that failed processing.
 * Uses a 3-dot dropdown menu for actions (rename, download, delete).
 */

import React from 'react';
import {
  FileText,
  File,
  MusicNote,
  Image,
  Table,
  Trash,
  DownloadSimple,
  Link,
  CircleNotch,
  Warning,
  CheckCircle,
  DotsThreeVertical,
  PencilSimple,
  Stop,
  ArrowClockwise,
} from '@phosphor-icons/react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { Checkbox } from '../ui/checkbox';
import { formatFileSize, type Source } from '../../lib/api/sources';

interface SourceItemProps {
  source: Source;
  onDownload: (sourceId: string) => void;
  onDelete: (sourceId: string, sourceName: string) => void;
  onRename: (sourceId: string, currentName: string) => void;
  onToggleActive: (sourceId: string, active: boolean) => void;
  onCancelProcessing: (sourceId: string) => void;
  onRetryProcessing: (sourceId: string) => void;
}

/**
 * Get the appropriate icon component for a source category
 */
const getCategoryIconComponent = (category: string) => {
  switch (category) {
    case 'document':
      return FileText;
    case 'audio':
      return MusicNote;
    case 'image':
      return Image;
    case 'data':
      return Table;
    case 'link':
      return Link;
    default:
      return File;
  }
};

/**
 * Get status display info (icon, color, text)
 * Educational Note: Different statuses indicate processing state:
 * - uploaded: Waiting to be processed (could be fresh upload or cancelled)
 * - processing: Currently extracting text from PDF
 * - embedding: Creating vector embeddings for semantic search
 * - ready: Successfully processed, available for chat
 * - error: Processing failed completely (no partial states - clean failure)
 */
const getStatusDisplay = (status: Source['status']) => {
  switch (status) {
    case 'uploaded':
      // Uploaded but not yet processing - could be cancelled or waiting
      return {
        icon: ArrowClockwise,
        color: 'text-muted-foreground',
        animate: false,
        tooltip: 'Ready to process',
      };
    case 'processing':
      return {
        icon: CircleNotch,
        color: 'text-amber-500',
        animate: true,
        tooltip: 'Processing...',
      };
    case 'embedding':
      // Creating embeddings for semantic search
      return {
        icon: CircleNotch,
        color: 'text-blue-500',
        animate: true,
        tooltip: 'Embedding...',
      };
    case 'ready':
      return {
        icon: CheckCircle,
        color: 'text-green-600',
        animate: false,
        tooltip: 'Ready',
      };
    case 'error':
      return {
        icon: Warning,
        color: 'text-destructive',
        animate: false,
        tooltip: 'Processing failed',
      };
    default:
      return null;
  }
};

export const SourceItem: React.FC<SourceItemProps> = ({
  source,
  onDownload,
  onDelete,
  onRename,
  onToggleActive,
  onCancelProcessing,
  onRetryProcessing,
}) => {
  const Icon = getCategoryIconComponent(source.category);
  const statusDisplay = getStatusDisplay(source.status);
  // "processing" or "embedding" are actively working - show spinner and allow cancel
  const isProcessing = source.status === 'processing';
  const isEmbedding = source.status === 'embedding';
  const isActivelyWorking = isProcessing || isEmbedding;
  // "uploaded" status means source is waiting for processing (fresh upload or cancelled)
  const isWaitingToProcess = source.status === 'uploaded';
  // Source can be toggled active/inactive only when it's ready
  // Educational Note: No partial status - sources are either fully ready or failed
  const canToggleActive = source.status === 'ready';

  return (
    <div
      className={`grid grid-cols-[auto_1fr_auto_auto] items-center gap-2 p-2 rounded-lg hover:bg-accent group transition-colors ${
        isActivelyWorking ? 'opacity-60' : ''
      }`}
    >
      {/* Icon Area - Shows category icon, transforms to menu on hover */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded hover:bg-muted transition-colors">
            {/* Category icon - visible by default, hidden on hover */}
            <Icon
              size={16}
              className="text-muted-foreground group-hover:hidden"
            />
            {/* Menu icon - hidden by default, visible on hover */}
            <DotsThreeVertical
              size={16}
              weight="bold"
              className="text-muted-foreground hidden group-hover:block"
            />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          {/* Retry/Start option - for error or uploaded (waiting) state */}
          {(source.status === 'error' || isWaitingToProcess) && (
            <DropdownMenuItem onClick={() => onRetryProcessing(source.id)}>
              <ArrowClockwise size={14} className="mr-2" />
              {isWaitingToProcess ? 'Start Processing' : 'Retry Processing'}
            </DropdownMenuItem>
          )}

          {/* Stop option - only for actively working state (processing or embedding) */}
          {isActivelyWorking && (
            <DropdownMenuItem onClick={() => onCancelProcessing(source.id)}>
              <Stop size={14} className="mr-2" />
              {isEmbedding ? 'Stop Embedding' : 'Stop Processing'}
            </DropdownMenuItem>
          )}

          {/* Rename option - disabled during active work */}
          <DropdownMenuItem
            onClick={() => onRename(source.id, source.name)}
            disabled={isActivelyWorking}
          >
            <PencilSimple size={14} className="mr-2" />
            Rename
          </DropdownMenuItem>

          {/* Download option - disabled during active work */}
          <DropdownMenuItem
            onClick={() => onDownload(source.id)}
            disabled={isActivelyWorking}
          >
            <DownloadSimple size={14} className="mr-2" />
            Download
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          {/* Delete option */}
          <DropdownMenuItem
            onClick={() => onDelete(source.id, source.name)}
            className="text-destructive focus:text-destructive"
          >
            <Trash size={14} className="mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Source Info - truncates when panel is narrow, expands when resized */}
      <div className="overflow-hidden">
        <p className="text-sm truncate" title={source.name}>
          {source.name}
        </p>
        <div className="flex items-center gap-2">
          <p className="text-xs text-muted-foreground">
            {formatFileSize(source.file_size)}
          </p>
          {/* Status indicator text for non-ready states */}
          {source.status !== 'ready' && statusDisplay && (
            <span className={`text-xs ${statusDisplay.color}`}>
              {statusDisplay.tooltip}
            </span>
          )}
        </div>
      </div>

      {/* Active Checkbox - only enabled for ready/partial sources */}
      <Checkbox
        checked={source.active}
        onCheckedChange={(checked) => onToggleActive(source.id, checked === true)}
        disabled={!canToggleActive}
        className={`flex-shrink-0 ${!canToggleActive ? 'opacity-30' : ''}`}
        title={canToggleActive ? (source.active ? 'Click to exclude from chat' : 'Click to include in chat') : 'Source must be processed first'}
      />

      {/* Status Icon for non-ready states */}
      {statusDisplay && source.status !== 'ready' && (
        <>
          {isActivelyWorking ? (
            // Processing or Embedding state: show spinner by default, stop icon on hover
            <button
              onClick={() => onCancelProcessing(source.id)}
              className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded hover:bg-destructive/10 transition-colors"
              title={isEmbedding ? 'Click to stop embedding' : 'Click to stop processing'}
            >
              {/* Spinner - visible by default, hidden on hover */}
              <CircleNotch
                size={16}
                className={`${isEmbedding ? 'text-blue-500' : 'text-amber-500'} animate-spin group-hover:hidden`}
              />
              {/* Stop icon - hidden by default, visible on hover */}
              <Stop
                size={16}
                weight="fill"
                className="text-destructive hidden group-hover:block"
              />
            </button>
          ) : isWaitingToProcess ? (
            // Uploaded/cancelled state: show retry icon to start processing
            <button
              onClick={() => onRetryProcessing(source.id)}
              className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded hover:bg-amber-100 transition-colors"
              title="Click to start processing"
            >
              <ArrowClockwise
                size={16}
                weight="bold"
                className="text-muted-foreground group-hover:text-amber-600"
              />
            </button>
          ) : (
            // Error state: show warning icon with retry button
            <button
              onClick={() => onRetryProcessing(source.id)}
              className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded hover:bg-amber-100 transition-colors"
              title="Click to retry processing"
            >
              {/* Warning - visible by default, hidden on hover */}
              <Warning
                size={16}
                className="text-destructive group-hover:hidden"
              />
              {/* Retry icon - hidden by default, visible on hover */}
              <ArrowClockwise
                size={16}
                weight="bold"
                className="text-amber-600 hidden group-hover:block"
              />
            </button>
          )}
        </>
      )}
    </div>
  );
};
