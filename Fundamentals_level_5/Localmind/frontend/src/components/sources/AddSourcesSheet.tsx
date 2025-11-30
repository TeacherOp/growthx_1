/**
 * AddSourcesSheet Component
 * Educational Note: Sheet modal with tabs for different source upload methods.
 * Orchestrates UploadTab, LinkTab, and PasteTab components.
 */

import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { UploadTab } from './UploadTab';
import { LinkTab } from './LinkTab';
import { PasteTab } from './PasteTab';
import { GoogleDriveTab } from './GoogleDriveTab';
import { ResearchTab } from './ResearchTab';
import { MAX_SOURCES } from '../../lib/api/sources';

interface AddSourcesSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  sourcesCount: number;
  onUpload: (files: FileList | File[]) => Promise<void>;
  onAddUrl: (url: string) => Promise<void>;
  onAddText: (content: string, name: string) => Promise<void>;
  onAddResearch: (topic: string, description: string, links: string[]) => Promise<void>;
  onImportComplete: () => void;
  uploading: boolean;
}

export const AddSourcesSheet: React.FC<AddSourcesSheetProps> = ({
  open,
  onOpenChange,
  projectId,
  sourcesCount,
  onUpload,
  onAddUrl,
  onAddText,
  onAddResearch,
  onImportComplete,
  uploading,
}) => {
  const isAtLimit = sourcesCount >= MAX_SOURCES;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-[500px] sm:w-[600px]">
        <SheetHeader>
          <SheetTitle>Add sources</SheetTitle>
        </SheetHeader>

        <div className="mt-6">
          <p className="text-sm text-muted-foreground mb-4">
            Sources let LocalMind base its responses on the information that
            matters most to you. ({sourcesCount}/{MAX_SOURCES} used)
          </p>

          <Tabs defaultValue="upload" className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="upload">Upload</TabsTrigger>
              <TabsTrigger value="link">Link</TabsTrigger>
              <TabsTrigger value="paste">Paste</TabsTrigger>
              <TabsTrigger value="drive">Drive</TabsTrigger>
              <TabsTrigger value="research">Research</TabsTrigger>
            </TabsList>

            <TabsContent value="upload" className="mt-6">
              <UploadTab
                onUpload={onUpload}
                uploading={uploading}
                isAtLimit={isAtLimit}
              />
            </TabsContent>

            <TabsContent value="link" className="mt-6">
              <LinkTab onAddUrl={onAddUrl} isAtLimit={isAtLimit} />
            </TabsContent>

            <TabsContent value="paste" className="mt-6">
              <PasteTab onAddText={onAddText} isAtLimit={isAtLimit} />
            </TabsContent>

            <TabsContent value="drive" className="mt-6">
              <GoogleDriveTab
                projectId={projectId}
                onImportComplete={() => {
                  onImportComplete();
                  onOpenChange(false); // Close sheet after import
                }}
                isAtLimit={isAtLimit}
              />
            </TabsContent>

            <TabsContent value="research" className="mt-6">
              <ResearchTab
                onAddResearch={onAddResearch}
                isAtLimit={isAtLimit}
              />
            </TabsContent>
          </Tabs>
        </div>
      </SheetContent>
    </Sheet>
  );
};
