import React, { useState, useEffect } from 'react';
import { Plus, FolderOpen, Trash, Clock } from '@phosphor-icons/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription, EmptyContent } from './ui/empty';
import { projectsAPI } from '@/lib/api';

/**
 * ProjectList Component
 * Educational Note: This component displays all projects and handles
 * project selection. It demonstrates React hooks (useState, useEffect)
 * and async data fetching patterns.
 */

interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  last_accessed: string;
}

interface ProjectListProps {
  onSelectProject: (project: Project) => void;
  onCreateNew: () => void;
  refreshTrigger?: number; // Used to refresh the list when projects change
}

export const ProjectList: React.FC<ProjectListProps> = ({
  onSelectProject,
  onCreateNew,
  refreshTrigger = 0
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch projects from API
  useEffect(() => {
    loadProjects();
  }, [refreshTrigger]); // Re-fetch when refreshTrigger changes

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await projectsAPI.list();
      setProjects(response.data.projects || []);
    } catch (err) {
      setError('Failed to load projects');
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenProject = async (project: Project) => {
    try {
      // Mark project as opened
      await projectsAPI.open(project.id);
      // Select the project
      onSelectProject(project);
    } catch (err) {
      console.error('Error opening project:', err);
    }
  };

  const handleDeleteProject = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation(); // Prevent card click

    if (confirm('Are you sure you want to delete this project?')) {
      try {
        await projectsAPI.delete(projectId);
        loadProjects(); // Refresh the list
      } catch (err) {
        console.error('Error deleting project:', err);
        alert('Failed to delete project');
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading projects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={loadProjects}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Projects</h2>
          <p className="text-muted-foreground">
            Your knowledge workspaces • {projects.length} total
          </p>
        </div>
        <Button onClick={onCreateNew} size="lg">
          <Plus size={20} className="mr-2" />
          Create New Project
        </Button>
      </div>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <FolderOpen size={24} />
            </EmptyMedia>
            <EmptyTitle>No projects yet</EmptyTitle>
            <EmptyDescription>
              Create your first project to get started
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button onClick={onCreateNew}>
              <Plus size={16} className="mr-2" />
              Create First Project
            </Button>
          </EmptyContent>
        </Empty>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleOpenProject(project)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{project.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {project.description || 'No description'}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => handleDeleteProject(e, project.id)}
                    className="ml-2"
                  >
                    <Trash size={16} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Clock size={12} className="mr-1" />
                  Last opened: {formatDate(project.last_accessed)}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};