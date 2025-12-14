/**
 * ProcessedContentSheet Component
 * Educational Note: Sheet modal for viewing processed/extracted text from sources.
 * Displays the full extracted content with page markers in a scrollable view.
 * Only shows for text-based sources (PDF, DOCX, PPTX, TXT, Link, YouTube, Research).
 */

import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../ui/sheet';
import { ScrollArea } from '../ui/scroll-area';

interface ProcessedContentSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceName: string;
  content: string;
}

export const ProcessedContentSheet: React.FC<ProcessedContentSheetProps> = ({
  open,
  onOpenChange,
  sourceName,
  content,
}) => {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-[500px] sm:w-[600px] flex flex-col">
        <SheetHeader>
          <SheetTitle className="truncate" title={sourceName}>
            {sourceName}
          </SheetTitle>
        </SheetHeader>

        <ScrollArea className="flex-1 mt-4 pr-4">
          <pre className="text-sm whitespace-pre-wrap font-mono text-foreground/90 leading-relaxed">
            {content}
          </pre>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
};
