import { useState } from 'react';
import { ProjectList } from './components/ProjectList';
import { CreateProjectDialog } from './components/CreateProjectDialog';

/**
 * Main App Component for LocalMind
 * Educational Note: This component manages the overall application state
 * and controls which view is shown (project list, create dialog, or project view).
 */

function App() {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleProjectCreated = (project: any) => {
    console.log('Project created/updated:', project);
    setShowCreateDialog(false);
    // Trigger refresh of project list
    setRefreshTrigger(prev => prev + 1);
  };

  const handleSelectProject = (project: any) => {
    console.log('Project selected:', project);
    setSelectedProject(project);
    // TODO: Navigate to project workspace
  };

  // If a project is selected, show the project workspace (TODO)
  if (selectedProject) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto p-8">
          <div className="mb-4">
            <button
              onClick={() => setSelectedProject(null)}
              className="text-primary hover:underline"
            >
              ← Back to Projects
            </button>
          </div>
          <h1 className="text-3xl font-bold mb-4">{selectedProject.name}</h1>
          <p className="text-muted-foreground">{selectedProject.description}</p>
          <div className="mt-8 p-8 border rounded-lg">
            <p className="text-center text-muted-foreground">
              Project workspace coming soon...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <ProjectList
        onSelectProject={handleSelectProject}
        onCreateNew={() => setShowCreateDialog(true)}
        refreshTrigger={refreshTrigger}
      />

      {showCreateDialog && (
        <CreateProjectDialog
          onClose={() => setShowCreateDialog(false)}
          onProjectCreated={handleProjectCreated}
        />
      )}
    </div>
  );
}

export default App
