/**
 * SourcesList Component
 * Educational Note: Displays the list of sources with loading and empty states.
 * Uses ScrollArea for scrollable content and renders SourceItem for each source.
 */

import React from 'react';
import { ScrollArea } from '../ui/scroll-area';
import { CircleNotch, FolderOpen } from '@phosphor-icons/react';
import { type Source } from '../../lib/api/sources';
import { SourceItem } from './SourceItem';

interface SourcesListProps {
  sources: Source[];
  loading: boolean;
  searchQuery: string;
  onDownload: (sourceId: string) => void;
  onDelete: (sourceId: string, sourceName: string) => void;
  onRename: (sourceId: string, currentName: string) => void;
  onToggleActive: (sourceId: string, active: boolean) => void;
  onCancelProcessing: (sourceId: string) => void;
  onRetryProcessing: (sourceId: string) => void;
}

export const SourcesList: React.FC<SourcesListProps> = ({
  sources,
  loading,
  searchQuery,
  onDownload,
  onDelete,
  onRename,
  onToggleActive,
  onCancelProcessing,
  onRetryProcessing,
}) => {
  // Filter sources based on search
  const filteredSources = sources.filter((source) =>
    source.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <ScrollArea className="flex-1">
      <div className="p-4">
        {loading ? (
          <div className="text-center py-8">
            <CircleNotch size={32} className="mx-auto mb-3 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading sources...</p>
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FolderOpen size={48} className="mx-auto mb-3 opacity-50" />
            <p className="text-sm">
              {searchQuery ? 'No sources match your search' : 'No sources yet'}
            </p>
            <p className="text-xs mt-1">
              {searchQuery
                ? 'Try a different search term'
                : 'Add documents, images, or audio to get started'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredSources.map((source) => (
              <SourceItem
                key={source.id}
                source={source}
                onDownload={onDownload}
                onDelete={onDelete}
                onRename={onRename}
                onToggleActive={onToggleActive}
                onCancelProcessing={onCancelProcessing}
                onRetryProcessing={onRetryProcessing}
              />
            ))}
          </div>
        )}
      </div>
    </ScrollArea>
  );
};
