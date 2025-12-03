/**
 * WebsiteViewerModal Component
 * Educational Note: Modal for previewing generated websites in an iframe.
 * Simpler than component viewer since websites are single-page previews.
 */

import React from 'react';
import { DownloadSimple, Globe } from '@phosphor-icons/react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../../ui/dialog';
import { websitesAPI, type WebsiteJob } from '@/lib/api/studio';

interface WebsiteViewerModalProps {
  projectId: string;
  viewingWebsiteJob: WebsiteJob | null;
  onClose: () => void;
}

export const WebsiteViewerModal: React.FC<WebsiteViewerModalProps> = ({
  projectId,
  viewingWebsiteJob,
  onClose,
}) => {
  if (!viewingWebsiteJob) return null;

  const previewUrl = websitesAPI.getPreviewUrl(projectId, viewingWebsiteJob.id);
  const downloadUrl = websitesAPI.getDownloadUrl(projectId, viewingWebsiteJob.id);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `${viewingWebsiteJob.site_name || 'website'}.zip`;
    link.click();
  };

  const handleOpenInNewTab = () => {
    window.open(previewUrl, '_blank');
  };

  return (
    <Dialog open={!!viewingWebsiteJob} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-6xl h-[85vh] p-0 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex-shrink-0">
          <DialogHeader className="mb-2">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-purple-500/10 rounded">
                <Globe size={20} weight="duotone" className="text-purple-600" />
              </div>
              <div>
                <DialogTitle className="text-lg">
                  {viewingWebsiteJob.site_name || 'Website'}
                </DialogTitle>
              </div>
            </div>
            <DialogDescription>
              {viewingWebsiteJob.pages_created?.length || 0} pages • {viewingWebsiteJob.features_implemented?.length || 0} features
            </DialogDescription>
          </DialogHeader>

          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenInNewTab}
              className="px-3 py-1.5 text-xs bg-purple-500/10 hover:bg-purple-500/20 text-purple-700 rounded transition-colors flex items-center gap-1.5"
            >
              <Globe size={14} />
              Open in New Tab
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-1.5 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors flex items-center gap-1.5"
            >
              <DownloadSimple size={14} />
              Download ZIP
            </button>
          </div>
        </div>

        {/* Website Preview */}
        <div className="flex-1 min-h-0 bg-gray-50">
          <iframe
            src={previewUrl}
            className="w-full h-full border-0"
            title={viewingWebsiteJob.site_name || 'Website Preview'}
            sandbox="allow-scripts allow-same-origin allow-forms allow-modals"
          />
        </div>

        {/* Footer Info */}
        {viewingWebsiteJob.summary && (
          <div className="px-6 py-3 border-t bg-gray-50/50 flex-shrink-0">
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">Summary:</span> {viewingWebsiteJob.summary}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
