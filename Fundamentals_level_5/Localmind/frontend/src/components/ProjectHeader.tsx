import React, { useEffect } from 'react';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { ArrowLeft, DotsThreeVertical, Plus, Trash, FolderOpen, Gear, CircleNotch } from '@phosphor-icons/react';
import { chatsAPI } from '../lib/api/chats';
import { useToast, ToastContainer } from './ui/toast';

/**
 * ProjectHeader Component
 * Educational Note: Header for project workspace with navigation and project actions.
 * Now loads and saves the system prompt using the real API.
 */

interface ProjectHeaderProps {
  project: {
    id: string;
    name: string;
    description?: string;
  };
  onBack: () => void;
  onDelete: () => void;
}

export const ProjectHeader: React.FC<ProjectHeaderProps> = ({
  project,
  onBack,
  onDelete,
}) => {
  const { toasts, dismissToast, success, error } = useToast();

  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = React.useState(false);

  // System prompt state (dictation prompt removed - ElevenLabs doesn't support prompt parameter)
  const [systemPrompt, setSystemPrompt] = React.useState('');
  const [tempSystemPrompt, setTempSystemPrompt] = React.useState('');
  const [defaultPrompt, setDefaultPrompt] = React.useState('');

  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  /**
   * Educational Note: Load the project's system prompt when component mounts.
   * This fetches either the custom prompt or the default prompt from the backend.
   */
  useEffect(() => {
    loadPrompts();
  }, [project.id]);

  /**
   * Load system prompt for the project
   * Educational Note: Dictation prompt removed - ElevenLabs doesn't support prompt parameter
   */
  const loadPrompts = async () => {
    try {
      setLoading(true);

      // Load system prompts in parallel
      const [projectPrompt, defaultPromptText] = await Promise.all([
        chatsAPI.getProjectPrompt(project.id),
        chatsAPI.getDefaultPrompt(),
      ]);

      // Set system prompt state
      setSystemPrompt(projectPrompt);
      setDefaultPrompt(defaultPromptText);
    } catch (err) {
      console.error('Error loading prompts:', err);
      error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleNewProject = () => {
    console.log('Creating new project...');
    // For now, just navigate back to project list
    onBack();
  };

  const handleOpenSettings = () => {
    setTempSystemPrompt(systemPrompt);
    setSettingsDialogOpen(true);
  };

  /**
   * Educational Note: Save the system prompt to the backend.
   * If prompt matches default, we save null to reset to default.
   */
  const handleSaveSettings = async () => {
    try {
      setSaving(true);

      // Determine if prompt is custom or should reset to default
      const systemPromptToSave = tempSystemPrompt === defaultPrompt ? null : tempSystemPrompt;

      console.log('Saving settings for project:', project.id);

      // Save system prompt
      const systemResult = await chatsAPI.updateProjectPrompt(project.id, systemPromptToSave);

      // Update local state
      setSystemPrompt(systemResult.prompt);
      setSettingsDialogOpen(false);

      success('Settings saved successfully');
    } catch (err) {
      console.error('Error saving settings:', err);
      error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleResetSystemPrompt = () => {
    setTempSystemPrompt(defaultPrompt);
  };

  return (
    <div className="h-14 border-b flex items-center justify-between px-4 bg-background">
      {/* Left side - Back button and project name */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onBack}
          className="h-8 w-8"
        >
          <ArrowLeft size={16} />
        </Button>

        <div className="flex items-center gap-2">
          <FolderOpen size={20} className="text-muted-foreground" />
          <h1 className="text-lg font-semibold">{project.name}</h1>
        </div>
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleOpenSettings}
          className="gap-2"
        >
          <Gear size={16} />
          Project Settings
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleNewProject}
          className="gap-2"
        >
          <Plus size={16} />
          New Project
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <DotsThreeVertical size={16} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => console.log('Rename project')}>
              Rename Project
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => console.log('Duplicate project')}>
              Duplicate Project
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => console.log('Export project')}>
              Export Project
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash size={16} className="mr-2" />
              Delete Project
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete "{project.name}" and all of its data.
              This action cannot be undone. All sources, chats, and generated content
              will be lost forever.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onDelete();
                setDeleteDialogOpen(false);
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Project
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Project Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Project Settings</DialogTitle>
            <DialogDescription>
              Configure settings for "{project.name}"
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <CircleNotch size={24} className="animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading settings...</span>
              </div>
            ) : (
              <>
                {/* System Prompt Section */}
                <div className="space-y-2">
                  <Label htmlFor="system-prompt">
                    System Prompt (AI Chat)
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    This prompt defines how the AI assistant behaves when responding to queries about this project.
                  </p>
                  <Textarea
                    id="system-prompt"
                    value={tempSystemPrompt}
                    onChange={(e) => setTempSystemPrompt(e.target.value)}
                    className="h-48 font-mono resize-none"
                    placeholder="Enter system prompt..."
                    disabled={saving}
                  />
                  <div className="flex justify-between items-center">
                    <p className="text-xs text-muted-foreground">
                      {tempSystemPrompt.length} characters
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleResetSystemPrompt}
                      disabled={tempSystemPrompt === defaultPrompt || saving}
                    >
                      Reset to Default
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                tempSystemPrompt === systemPrompt ||
                saving ||
                loading
              }
            >
              {saving ? (
                <>
                  <CircleNotch size={16} className="mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};