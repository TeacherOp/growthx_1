/**
 * GoogleDriveTab Component
 * Educational Note: Tab content for importing files from Google Drive.
 * Shows file browser when connected, or setup instructions when not.
 * Click on files to import (with confirmation dialog), click folders to navigate.
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog';
import {
  GoogleDriveLogo,
  Folder,
  File,
  FileDoc,
  FileXls,
  FilePpt,
  FilePdf,
  FileImage,
  FileAudio,
  ArrowLeft,
  CircleNotch,
  Gear,
} from '@phosphor-icons/react';
import { googleDriveAPI, type GoogleFile, type GoogleStatus } from '@/lib/api/settings';
import { useToast } from '../ui/toast';

interface GoogleDriveTabProps {
  projectId: string;
  onImportComplete: () => void;
  isAtLimit: boolean;
}

export const GoogleDriveTab: React.FC<GoogleDriveTabProps> = ({
  projectId,
  onImportComplete,
  isAtLimit,
}) => {
  const [status, setStatus] = useState<GoogleStatus>({
    configured: false,
    connected: false,
    email: null,
  });
  const [files, setFiles] = useState<GoogleFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState<string | null>(null);
  const [folderStack, setFolderStack] = useState<{ id: string | null; name: string }[]>([
    { id: null, name: 'My Drive' },
  ]);

  // Confirmation dialog state
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<GoogleFile | null>(null);

  const { success, error } = useToast();

  // Load Google status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  // Load files when connected or folder changes
  useEffect(() => {
    if (status.connected) {
      loadFiles();
    }
  }, [status.connected, folderStack]);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const googleStatus = await googleDriveAPI.getStatus();
      setStatus(googleStatus);
    } catch (err) {
      console.error('Error loading Google status:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadFiles = async () => {
    setLoading(true);
    try {
      const currentFolder = folderStack[folderStack.length - 1];
      const result = await googleDriveAPI.listFiles(currentFolder.id || undefined);
      if (result.success) {
        setFiles(result.files);
      } else {
        error(result.error || 'Failed to load files');
      }
    } catch (err) {
      console.error('Error loading files:', err);
      error('Failed to load Google Drive files');
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = (file: GoogleFile) => {
    setFolderStack([...folderStack, { id: file.id, name: file.name }]);
  };

  const handleBack = () => {
    if (folderStack.length > 1) {
      setFolderStack(folderStack.slice(0, -1));
    }
  };

  /**
   * Handle file click - open confirmation dialog
   */
  const handleFileClick = (file: GoogleFile) => {
    if (file.is_folder) {
      handleFolderClick(file);
    } else {
      if (isAtLimit) {
        error('Source limit reached');
        return;
      }
      setSelectedFile(file);
      setConfirmDialogOpen(true);
    }
  };

  /**
   * Confirm import and execute
   */
  const handleConfirmImport = async () => {
    if (!selectedFile) return;

    setConfirmDialogOpen(false);
    setImporting(selectedFile.id);

    try {
      const result = await googleDriveAPI.importFile(projectId, selectedFile.id, selectedFile.name);
      if (result.success) {
        success(`Imported ${selectedFile.name}`);
        onImportComplete();
      } else {
        error(result.error || 'Failed to import file');
      }
    } catch (err) {
      console.error('Error importing file:', err);
      error('Failed to import file');
    } finally {
      setImporting(null);
      setSelectedFile(null);
    }
  };

  const getFileIcon = (file: GoogleFile) => {
    if (file.is_folder) return <Folder size={20} weight="fill" className="text-amber-500" />;
    if (file.mime_type.includes('document') || file.google_type === 'Google Doc')
      return <FileDoc size={20} weight="fill" className="text-blue-500" />;
    if (file.mime_type.includes('spreadsheet') || file.google_type === 'Google Sheet')
      return <FileXls size={20} weight="fill" className="text-green-500" />;
    if (file.mime_type.includes('presentation') || file.google_type === 'Google Slides')
      return <FilePpt size={20} weight="fill" className="text-orange-500" />;
    if (file.mime_type.includes('pdf'))
      return <FilePdf size={20} weight="fill" className="text-red-500" />;
    if (file.mime_type.startsWith('image/'))
      return <FileImage size={20} weight="fill" className="text-purple-500" />;
    if (file.mime_type.startsWith('audio/'))
      return <FileAudio size={20} weight="fill" className="text-pink-500" />;
    return <File size={20} weight="fill" className="text-stone-400" />;
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Not configured state
  if (!loading && !status.configured) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <GoogleDriveLogo size={48} weight="duotone" className="text-muted-foreground mb-4" />
        <h3 className="font-medium mb-2">Google Drive Not Configured</h3>
        <p className="text-sm text-muted-foreground mb-4 max-w-sm">
          Add your Google Client ID and Client Secret in App Settings to enable Google Drive
          integration.
        </p>
        <Button variant="outline" size="sm">
          <Gear size={16} className="mr-2" />
          Open Settings
        </Button>
      </div>
    );
  }

  // Not connected state
  if (!loading && !status.connected) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <GoogleDriveLogo size={48} weight="duotone" className="text-amber-600 mb-4" />
        <h3 className="font-medium mb-2">Connect Google Drive</h3>
        <p className="text-sm text-muted-foreground mb-4 max-w-sm">
          Connect your Google account in App Settings to import files from Google Drive.
        </p>
        <Button variant="outline" size="sm">
          <Gear size={16} className="mr-2" />
          Open Settings
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with breadcrumb */}
      <div className="flex items-center gap-2">
        {folderStack.length > 1 && (
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft size={16} />
          </Button>
        )}
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          {folderStack.map((folder, i) => (
            <React.Fragment key={folder.id || 'root'}>
              {i > 0 && <span>/</span>}
              <span className={i === folderStack.length - 1 ? 'font-medium text-foreground' : ''}>
                {folder.name}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* File list */}
      <ScrollArea className="h-[350px] border rounded-lg">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <CircleNotch size={24} className="animate-spin text-muted-foreground" />
          </div>
        ) : files.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Folder size={32} className="mb-2" />
            <p className="text-sm">No files found</p>
          </div>
        ) : (
          <div className="divide-y">
            {files.map((file) => (
              <div
                key={file.id}
                className={`grid grid-cols-[auto_1fr] items-center gap-3 p-3 hover:bg-muted/50 cursor-pointer transition-colors ${
                  importing === file.id ? 'opacity-50 pointer-events-none' : ''
                }`}
                onClick={() => handleFileClick(file)}
              >
                {/* File icon */}
                <div className="flex-shrink-0">
                  {importing === file.id ? (
                    <CircleNotch size={20} className="animate-spin text-amber-600" />
                  ) : (
                    getFileIcon(file)
                  )}
                </div>
                {/* File info - truncates properly */}
                <div className="overflow-hidden">
                  <p className="text-sm font-medium truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {file.is_google_file && file.google_type && (
                      <span className="mr-2">{file.google_type}</span>
                    )}
                    {file.size && formatFileSize(file.size)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Footer info */}
      <p className="text-xs text-muted-foreground">
        Connected as {status.email}. Click on folders to navigate, click files to import.
      </p>

      {/* Import Confirmation Dialog */}
      <AlertDialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Import from Google Drive</AlertDialogTitle>
            <AlertDialogDescription>
              {selectedFile && (
                <>
                  Import <span className="font-medium text-foreground">{selectedFile.name}</span>
                  {selectedFile.is_google_file && selectedFile.export_extension && (
                    <span className="text-muted-foreground">
                      {' '}(will be converted to {selectedFile.export_extension.toUpperCase().replace('.', '')})
                    </span>
                  )}
                  {' '}to your sources?
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedFile(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmImport}>Import</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
