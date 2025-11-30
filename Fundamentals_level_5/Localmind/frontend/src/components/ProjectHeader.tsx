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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import { ArrowLeft, DotsThreeVertical, Plus, Trash, FolderOpen, Gear, CircleNotch, CurrencyDollar, Brain } from '@phosphor-icons/react';
import { chatsAPI } from '../lib/api/chats';
import { projectsAPI, type CostTracking, type MemoryData } from '../lib/api';
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
  costsVersion?: number; // Increment to trigger cost refresh
}

export const ProjectHeader: React.FC<ProjectHeaderProps> = ({
  project,
  onBack,
  onDelete,
  costsVersion,
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

  // Cost tracking state
  const [costs, setCosts] = React.useState<CostTracking | null>(null);

  // Memory state
  const [memoryDialogOpen, setMemoryDialogOpen] = React.useState(false);
  const [memory, setMemory] = React.useState<MemoryData | null>(null);
  const [loadingMemory, setLoadingMemory] = React.useState(false);

  /**
   * Educational Note: Load the project's system prompt and costs when component mounts.
   * This fetches either the custom prompt or the default prompt from the backend.
   */
  useEffect(() => {
    loadPrompts();
    loadCosts();
  }, [project.id]);

  /**
   * Refresh costs when costsVersion changes (triggered after chat messages)
   * Educational Note: Uses version counter pattern for cross-component updates
   */
  useEffect(() => {
    if (costsVersion !== undefined && costsVersion > 0) {
      loadCosts();
    }
  }, [costsVersion]);

  /**
   * Load project cost tracking data
   * Educational Note: Costs are tracked cumulatively in project.json
   */
  const loadCosts = async () => {
    try {
      const response = await projectsAPI.getCosts(project.id);
      if (response.data.success) {
        setCosts(response.data.costs);
      }
    } catch (err) {
      console.error('Error loading costs:', err);
      // Silently fail - costs are not critical
    }
  };

  /**
   * Load memory data (user + project memory)
   * Educational Note: Memory is loaded when user opens the memory dialog.
   */
  const loadMemory = async () => {
    try {
      setLoadingMemory(true);
      const response = await projectsAPI.getMemory(project.id);
      if (response.data.success) {
        setMemory(response.data.memory);
      }
    } catch (err) {
      console.error('Error loading memory:', err);
      error('Failed to load memory');
    } finally {
      setLoadingMemory(false);
    }
  };

  /**
   * Open memory dialog and load memory data
   * Educational Note: Memory is fetched on-demand when dialog opens.
   */
  const handleOpenMemory = () => {
    setMemoryDialogOpen(true);
    loadMemory();
  };

  /**
   * Format currency for header display (without $ symbol - icon provides it)
   */
  const formatCost = (cost: number): string => {
    if (cost < 0.01) {
      return '0.00';
    }
    return cost.toFixed(2);
  };

  /**
   * Format currency for tooltip with $ symbol
   */
  const formatCostWithSymbol = (cost: number): string => {
    if (cost < 0.01) {
      return '$0.00';
    }
    return `$${cost.toFixed(2)}`;
  };

  /**
   * Format token count with K suffix for thousands
   */
  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

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
    <div className="h-14 flex items-center justify-between px-4 bg-background">
      {/* Left side - Back button and project name */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
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

        {/* Cost Display with Hover Breakdown */}
        {costs && costs.total_cost > 0 && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1.5 px-2 py-1 bg-muted/50 rounded-md cursor-default">
                  <CurrencyDollar size={14} className="text-muted-foreground" />
                  <span className="text-sm text-muted-foreground font-medium">
                    {formatCost(costs.total_cost)}
                  </span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="p-3">
                <div className="space-y-2 text-xs">
                  <p className="font-semibold text-sm mb-2">API Usage Breakdown</p>

                  {/* Sonnet breakdown */}
                  {(costs.by_model.sonnet.input_tokens > 0 || costs.by_model.sonnet.output_tokens > 0) && (
                    <div className="space-y-1">
                      <p className="font-medium">Sonnet</p>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-muted-foreground">
                        <span>Input:</span>
                        <span>{formatTokens(costs.by_model.sonnet.input_tokens)} tokens</span>
                        <span>Output:</span>
                        <span>{formatTokens(costs.by_model.sonnet.output_tokens)} tokens</span>
                        <span>Cost:</span>
                        <span className="font-medium text-foreground">{formatCostWithSymbol(costs.by_model.sonnet.cost)}</span>
                      </div>
                    </div>
                  )}

                  {/* Haiku breakdown */}
                  {(costs.by_model.haiku.input_tokens > 0 || costs.by_model.haiku.output_tokens > 0) && (
                    <div className="space-y-1">
                      <p className="font-medium">Haiku</p>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-muted-foreground">
                        <span>Input:</span>
                        <span>{formatTokens(costs.by_model.haiku.input_tokens)} tokens</span>
                        <span>Output:</span>
                        <span>{formatTokens(costs.by_model.haiku.output_tokens)} tokens</span>
                        <span>Cost:</span>
                        <span className="font-medium text-foreground">{formatCostWithSymbol(costs.by_model.haiku.cost)}</span>
                      </div>
                    </div>
                  )}

                  <div className="border-t pt-2 mt-2">
                    <div className="flex justify-between font-medium">
                      <span>Total:</span>
                      <span>{formatCostWithSymbol(costs.total_cost)}</span>
                    </div>
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleOpenMemory}
          className="gap-2"
        >
          <Brain size={16} />
          Memory
        </Button>

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
            <Button variant="outline" size="icon" className="h-8 w-8 border-stone-300">
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

      {/* Memory Dialog */}
      <Dialog open={memoryDialogOpen} onOpenChange={setMemoryDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain size={20} />
              Memory
            </DialogTitle>
            <DialogDescription>
              Information the AI remembers about you and this project
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {loadingMemory ? (
              <div className="flex items-center justify-center py-8">
                <CircleNotch size={24} className="animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading memory...</span>
              </div>
            ) : (
              <>
                {/* User Memory Section */}
                <div className="space-y-2">
                  <Label>User Memory</Label>
                  <p className="text-xs text-muted-foreground">
                    Preferences and context that persist across all your projects
                  </p>
                  <div className="p-3 bg-muted/50 rounded-md min-h-[80px]">
                    {memory?.user_memory ? (
                      <p className="text-sm whitespace-pre-wrap">{memory.user_memory}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        No user memory stored yet. The AI will remember important details about you as you chat.
                      </p>
                    )}
                  </div>
                </div>

                {/* Project Memory Section */}
                <div className="space-y-2">
                  <Label>Project Memory</Label>
                  <p className="text-xs text-muted-foreground">
                    Context specific to "{project.name}"
                  </p>
                  <div className="p-3 bg-muted/50 rounded-md min-h-[80px]">
                    {memory?.project_memory ? (
                      <p className="text-sm whitespace-pre-wrap">{memory.project_memory}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        No project memory stored yet. The AI will remember important project-specific details as you chat.
                      </p>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setMemoryDialogOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};