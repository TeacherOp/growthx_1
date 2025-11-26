import React, { useState } from 'react';
import { Button } from './ui/button';
import { SourcesPanel } from './sources';
import { ChatPanel } from './ChatPanel';
import { StudioPanel } from './StudioPanel';
import { ProjectHeader } from './ProjectHeader';
import { CaretLeft, CaretRight } from '@phosphor-icons/react';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from './ui/resizable';

/**
 * ProjectWorkspace Component
 * Educational Note: This is the main workspace view for a project, inspired by NotebookLM.
 * It uses a three-panel layout: Sources (left), Chat (center), and Studio (right).
 * Panels can be collapsed/expanded for better focus.
 */

interface ProjectWorkspaceProps {
  project: {
    id: string;
    name: string;
    description: string;
  };
  onBack: () => void;
  onDeleteProject: (projectId: string) => void;
}

export const ProjectWorkspace: React.FC<ProjectWorkspaceProps> = ({
  project,
  onBack,
  onDeleteProject
}) => {
  // State for panel visibility
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Project Header */}
      <ProjectHeader
        project={project}
        onBack={onBack}
        onDelete={() => onDeleteProject(project.id)}
      />

      {/* Main Content Area - Resizable Panels */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left Panel - Sources (Resizable) */}
        <ResizablePanel
          defaultSize={20}
          minSize={15}
          maxSize={40}
          collapsible
          collapsedSize={3}
          onCollapse={() => setLeftPanelOpen(false)}
          onExpand={() => setLeftPanelOpen(true)}
          className="bg-muted/30"
        >
          {leftPanelOpen ? (
            <div className="h-full flex flex-col relative">
              <SourcesPanel projectId={project.id} />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setLeftPanelOpen(false)}
                className="absolute top-2 right-2 z-10 h-8 w-8"
              >
                <CaretLeft size={16} />
              </Button>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setLeftPanelOpen(true)}
                className="h-8 w-8"
              >
                <CaretRight size={16} />
              </Button>
            </div>
          )}
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Center Panel - Chat */}
        <ResizablePanel defaultSize={60} minSize={30}>
          <div className="h-full flex flex-col">
            <ChatPanel projectId={project.id} projectName={project.name} />
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right Panel - Studio (Resizable) */}
        <ResizablePanel
          defaultSize={20}
          minSize={15}
          maxSize={40}
          collapsible
          collapsedSize={3}
          onCollapse={() => setRightPanelOpen(false)}
          onExpand={() => setRightPanelOpen(true)}
          className="bg-muted/30"
        >
          {rightPanelOpen ? (
            <div className="h-full flex flex-col relative">
              <StudioPanel projectId={project.id} />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setRightPanelOpen(false)}
                className="absolute top-2 left-2 z-10 h-8 w-8"
              >
                <CaretRight size={16} />
              </Button>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setRightPanelOpen(true)}
                className="h-8 w-8"
              >
                <CaretLeft size={16} />
              </Button>
            </div>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};