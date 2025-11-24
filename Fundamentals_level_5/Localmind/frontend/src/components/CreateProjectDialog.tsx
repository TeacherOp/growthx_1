import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { projectsAPI } from '@/lib/api';

/**
 * CreateProjectDialog Component
 * Educational Note: This component handles project creation and editing.
 * It demonstrates controlled components (form inputs bound to state)
 * and form submission handling.
 */

interface CreateProjectDialogProps {
  onClose: () => void;
  onProjectCreated: (project: any) => void;
  editProject?: {
    id: string;
    name: string;
    description: string;
  } | null;
}

export const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  onClose,
  onProjectCreated,
  editProject = null
}) => {
  const [name, setName] = useState(editProject?.name || '');
  const [description, setDescription] = useState(editProject?.description || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError('Project name is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let response;

      if (editProject) {
        // Update existing project
        response = await projectsAPI.update(editProject.id, {
          name: name.trim(),
          description: description.trim()
        });
      } else {
        // Create new project
        response = await projectsAPI.create({
          name: name.trim(),
          description: description.trim()
        });
      }

      onProjectCreated(response.data.project);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save project');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>
              {editProject ? 'Edit Project' : 'Create New Project'}
            </CardTitle>
            <CardDescription>
              {editProject
                ? 'Update your project details'
                : 'Start a new project to organize your research and notes'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Project Name *
              </label>
              <Input
                id="name"
                placeholder="e.g., Q4 Research, Personal Notes"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium">
                Description (optional)
              </label>
              <Input
                id="description"
                placeholder="Brief description of your project"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={loading}
              />
            </div>

            {error && (
              <div className="text-sm text-destructive">
                {error}
              </div>
            )}
          </CardContent>

          <CardFooter className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading
                ? (editProject ? 'Updating...' : 'Creating...')
                : (editProject ? 'Update Project' : 'Create Project')
              }
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};