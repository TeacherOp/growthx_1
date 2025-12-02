import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { CreateProjectDialog } from './components/CreateProjectDialog';
import { ProjectWorkspace } from './components/ProjectWorkspace';
import { projectsAPI } from './lib/api';

/**
 * Main App Component for NoobBook
 * Educational Note: This component manages the overall application state
 * and controls which view is shown (project list, create dialog, or project workspace).
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
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await projectsAPI.delete(projectId);
      console.log('Project deleted successfully');
      setSelectedProject(null);
      setRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
  };

  // If a project is selected, show the project workspace
  if (selectedProject) {
    return (
      <ProjectWorkspace
        project={selectedProject}
        onBack={() => setSelectedProject(null)}
        onDeleteProject={handleDeleteProject}
      />
    );
  }

  return (
    <>
      <Dashboard
        onSelectProject={handleSelectProject}
        onCreateNewProject={() => setShowCreateDialog(true)}
        refreshTrigger={refreshTrigger}
      />

      {showCreateDialog && (
        <CreateProjectDialog
          onClose={() => setShowCreateDialog(false)}
          onProjectCreated={handleProjectCreated}
        />
      )}
    </>
  );
}

export default App
