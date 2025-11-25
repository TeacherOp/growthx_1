/**
 * SourcesPanel Component
 * Educational Note: Manages project sources (documents, images, audio, data files).
 * Uses Sheet component for slide-out modal and Tabs for different upload methods.
 * Connects to backend API for real source management.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from './ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Input } from './ui/input';
import { Progress } from './ui/progress';
import {
  Plus,
  Upload,
  FileText,
  FolderOpen,
  Video,
  ClipboardPaste,
  File,
  Search,
  Library,
  Music,
  Image,
  Table,
  Trash2,
  Loader2,
  Download,
  AlertCircle,
} from 'lucide-react';
import {
  sourcesAPI,
  formatFileSize,
  MAX_SOURCES,
  type Source,
} from '../lib/api/sources';
import { useToast, ToastContainer } from './ui/toast';

interface SourcesPanelProps {
  projectId: string;
}

/**
 * Get the appropriate icon component for a source category
 */
const getCategoryIconComponent = (category: string) => {
  switch (category) {
    case 'document':
      return FileText;
    case 'audio':
      return Music;
    case 'image':
      return Image;
    case 'data':
      return Table;
    default:
      return File;
  }
};

export const SourcesPanel: React.FC<SourcesPanelProps> = ({ projectId }) => {
  const { toasts, dismissToast, success, error } = useToast();

  // State
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Load sources from API
   */
  const loadSources = useCallback(async () => {
    try {
      setLoading(true);
      const data = await sourcesAPI.listSources(projectId);
      setSources(data);
    } catch (err) {
      console.error('Error loading sources:', err);
      error('Failed to load sources');
    } finally {
      setLoading(false);
    }
  }, [projectId, error]);

  // Load sources on mount and when projectId changes
  useEffect(() => {
    loadSources();
  }, [loadSources]);

  /**
   * Handle file upload
   */
  const handleFileUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);

    // Check source limit
    if (sources.length + fileArray.length > MAX_SOURCES) {
      error(`Cannot upload. Maximum ${MAX_SOURCES} sources allowed.`);
      return;
    }

    setUploading(true);

    try {
      for (const file of fileArray) {
        await sourcesAPI.uploadSource(projectId, file);
      }
      success(`Uploaded ${fileArray.length} file(s) successfully`);
      await loadSources();
      setSheetOpen(false);
    } catch (err: unknown) {
      console.error('Error uploading files:', err);
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      // Check if it's an axios error with response data
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosErr = err as { response?: { data?: { error?: string } } };
        error(axiosErr.response?.data?.error || errorMessage);
      } else {
        error(errorMessage);
      }
    } finally {
      setUploading(false);
    }
  };

  /**
   * Handle file input change
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files);
    }
  };

  /**
   * Handle drag events
   */
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  /**
   * Handle drop
   */
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  /**
   * Handle source deletion
   */
  const handleDeleteSource = async (sourceId: string, sourceName: string) => {
    try {
      await sourcesAPI.deleteSource(projectId, sourceId);
      success(`Deleted "${sourceName}"`);
      await loadSources();
    } catch (err) {
      console.error('Error deleting source:', err);
      error('Failed to delete source');
    }
  };

  /**
   * Handle source download
   */
  const handleDownloadSource = (sourceId: string) => {
    const url = sourcesAPI.getDownloadUrl(projectId, sourceId);
    window.open(url, '_blank');
  };

  // Filter sources based on search
  const filteredSources = sources.filter((source) =>
    source.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate totals
  const totalSize = sources.reduce((sum, s) => sum + s.file_size, 0);
  const sourcesCount = sources.length;
  const isAtLimit = sourcesCount >= MAX_SOURCES;

  return (
    <>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 pr-12 border-b">
          <div className="flex items-center gap-2 mb-3">
            <Library className="h-5 w-5 text-primary" />
            <h2 className="text-sm font-semibold">Sources</h2>
          </div>

          {/* Search */}
          <div className="relative mb-3">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search sources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>

          {/* Add Source Button */}
          <Button
            onClick={() => setSheetOpen(true)}
            className="w-full gap-2"
            variant="outline"
            size="sm"
            disabled={isAtLimit}
          >
            <Plus className="h-4 w-4" />
            Add sources
          </Button>
        </div>

        {/* Sources List */}
        <ScrollArea className="flex-1">
          <div className="p-4">
            {loading ? (
              <div className="text-center py-8">
                <Loader2 className="h-8 w-8 mx-auto mb-3 animate-spin text-muted-foreground" />
                <p className="text-sm text-muted-foreground">Loading sources...</p>
              </div>
            ) : filteredSources.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">
                  {searchQuery ? 'No sources match your search' : 'No sources yet'}
                </p>
                <p className="text-xs mt-1">
                  {searchQuery
                    ? 'Try a different search term'
                    : 'Add documents, images, or audio to get started'}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredSources.map((source) => {
                  const Icon = getCategoryIconComponent(source.category);
                  return (
                    <div
                      key={source.id}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-accent group transition-colors"
                    >
                      <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{source.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(source.file_size)}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleDownloadSource(source.id)}
                          title="Download"
                        >
                          <Download className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          onClick={() => handleDeleteSource(source.id, source.name)}
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer Stats with Limit */}
        <div className="p-4 border-t space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {sourcesCount} / {MAX_SOURCES} sources
            </span>
            <span>{formatFileSize(totalSize)} total</span>
          </div>
          <Progress value={(sourcesCount / MAX_SOURCES) * 100} className="h-1" />
          {isAtLimit && (
            <p className="text-xs text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Source limit reached
            </p>
          )}
        </div>
      </div>

      {/* Add Sources Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="left" className="w-[500px] sm:w-[600px]">
          <SheetHeader>
            <SheetTitle>Add sources</SheetTitle>
          </SheetHeader>

          <div className="mt-6">
            <p className="text-sm text-muted-foreground mb-4">
              Sources let LocalMind base its responses on the information that matters
              most to you. ({sourcesCount}/{MAX_SOURCES} used)
            </p>

            <Tabs defaultValue="upload" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="upload">Upload</TabsTrigger>
                <TabsTrigger value="link" disabled>
                  Link
                </TabsTrigger>
                <TabsTrigger value="paste" disabled>
                  Paste
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="mt-6">
                {/* Hidden file input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileInputChange}
                  accept=".pdf,.txt,.md,.mp3,.avif,.bmp,.gif,.ico,.jp2,.png,.webp,.tif,.tiff,.heic,.heif,.jpeg,.jpg,.jpe,.csv"
                />

                {/* Drag & Drop Zone */}
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? 'border-primary bg-primary/5'
                      : 'border-muted-foreground/25'
                  } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-10 w-10 mx-auto mb-4 text-primary animate-spin" />
                      <p className="text-sm font-medium mb-1">Uploading...</p>
                    </>
                  ) : (
                    <>
                      <Upload className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-sm font-medium mb-1">Upload sources</p>
                      <p className="text-xs text-muted-foreground mb-4">
                        Drag & drop or choose files to upload
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isAtLimit}
                      >
                        Choose Files
                      </Button>
                    </>
                  )}
                  <p className="text-xs text-muted-foreground mt-4">
                    Supported: PDF, TXT, Markdown, Audio (MP3), Images (PNG, JPG,
                    etc.), CSV
                  </p>
                </div>

                <Separator className="my-6" />

                <div className="space-y-3">
                  <Button
                    variant="outline"
                    className="w-full justify-start gap-3"
                    disabled
                    title="Coming soon"
                  >
                    <FolderOpen className="h-4 w-4" />
                    Google Drive (Coming soon)
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="link" className="mt-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Website URL
                    </label>
                    <div className="flex gap-2">
                      <Input placeholder="https://example.com" disabled />
                      <Button size="icon" variant="outline" disabled>
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Coming soon
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      YouTube Video
                    </label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="https://youtube.com/watch?v=..."
                        disabled
                      />
                      <Button size="icon" variant="outline" disabled>
                        <Video className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Coming soon
                    </p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="paste" className="mt-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Paste Text
                    </label>
                    <textarea
                      className="w-full h-32 p-3 border rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                      placeholder="Paste your text content here..."
                      disabled
                    />
                  </div>
                  <Button className="w-full" disabled>
                    <ClipboardPaste className="h-4 w-4 mr-2" />
                    Add Pasted Content (Coming soon)
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </SheetContent>
      </Sheet>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </>
  );
};
