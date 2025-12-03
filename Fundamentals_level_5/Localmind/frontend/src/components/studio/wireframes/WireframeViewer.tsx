/**
 * WireframeViewer Component
 * Educational Note: Renders wireframes using the Excalidraw React component.
 * We use convertToExcalidrawElements to convert skeleton elements to full
 * Excalidraw elements - this is the official way to create elements programmatically.
 */

import React, { useEffect, useState, useMemo } from 'react';
import { Excalidraw, convertToExcalidrawElements } from '@excalidraw/excalidraw';
import '@excalidraw/excalidraw/index.css';
import type { ExcalidrawElement } from '@/lib/api/studio/wireframes';

interface WireframeViewerProps {
  elements: ExcalidrawElement[];
  title?: string;
}

export const WireframeViewer: React.FC<WireframeViewerProps> = ({
  elements,
}) => {
  const [excalidrawAPI, setExcalidrawAPI] = useState<any>(null);

  // Convert our skeleton elements to full Excalidraw elements once
  const excalidrawElements = useMemo(() => {
    console.log('[WireframeViewer] Input elements:', elements.length);

    // Create minimal skeleton elements - only what's needed
    const skeletons = elements.map((elem) => {
      const base: any = {
        type: elem.type,
        x: elem.x ?? 0,
        y: elem.y ?? 0,
      };

      // Add styling if present
      if (elem.strokeColor) base.strokeColor = elem.strokeColor;
      if (elem.backgroundColor) base.backgroundColor = elem.backgroundColor;

      // Type-specific properties
      if (elem.type === 'text') {
        base.text = elem.text || 'Text';
        if (elem.fontSize) base.fontSize = elem.fontSize;
      } else if (elem.type === 'line' || elem.type === 'arrow') {
        base.points = elem.points || [[0, 0], [100, 0]];
      } else {
        base.width = elem.width ?? 100;
        base.height = elem.height ?? 50;
      }

      return base;
    });

    console.log('[WireframeViewer] Skeletons created:', skeletons.length);
    console.log('[WireframeViewer] First skeleton:', JSON.stringify(skeletons[0]));

    // Use Excalidraw's official conversion utility
    const converted = convertToExcalidrawElements(skeletons);
    console.log('[WireframeViewer] Converted elements:', converted.length);
    if (converted.length > 0) {
      console.log('[WireframeViewer] First converted:', JSON.stringify(converted[0]));
    }
    return converted;
  }, [elements]);

  // Scroll to content when ready
  useEffect(() => {
    if (excalidrawAPI && excalidrawElements.length > 0) {
      const timer = setTimeout(() => {
        excalidrawAPI.scrollToContent(excalidrawElements, { fitToViewport: true });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [excalidrawAPI, excalidrawElements]);

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <Excalidraw
        excalidrawAPI={(api) => setExcalidrawAPI(api)}
        initialData={{
          elements: excalidrawElements,
          appState: {
            viewBackgroundColor: '#ffffff',
          },
          scrollToContent: true,
        }}
      />
    </div>
  );
};
