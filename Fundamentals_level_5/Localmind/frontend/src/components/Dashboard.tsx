import React, { useState } from 'react';
import { ProjectList } from './ProjectList';
import { AppSettings } from './AppSettings';
import { Button } from './ui/button';
import {
  Settings,
  Brain
} from 'lucide-react';
import { ToastContainer, useToast } from './ui/toast';

/**
 * Dashboard Component
 * Educational Note: Main dashboard layout for the NotebookLM clone application.
 * This component manages the projects list and application settings.
 */

interface DashboardProps {
  onSelectProject: (project: any) => void;
  onCreateNewProject: () => void;
  refreshTrigger?: number;
}

export const Dashboard: React.FC<DashboardProps> = ({
  onSelectProject,
  onCreateNewProject,
  refreshTrigger = 0
}) => {
  const [appSettingsOpen, setAppSettingsOpen] = useState(false);
  const { toasts, dismissToast } = useToast();

  return (
    <div className="min-h-screen bg-background">
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">LocalLm</h1>
                <p className="text-xs text-muted-foreground">Your private AI knowledge hub</p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setAppSettingsOpen(true)}
              className="gap-2"
            >
              <Settings className="h-4 w-4" />
              App Settings
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <ProjectList
          onSelectProject={onSelectProject}
          onCreateNew={onCreateNewProject}
          refreshTrigger={refreshTrigger}
        />
      </main>

      {/* App Settings Dialog */}
      <AppSettings open={appSettingsOpen} onOpenChange={setAppSettingsOpen} />
    </div>
  );
};