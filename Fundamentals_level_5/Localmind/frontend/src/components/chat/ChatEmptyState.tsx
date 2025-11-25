/**
 * ChatEmptyState Component
 * Educational Note: Shown when no chats exist for a project.
 * Provides a clear call-to-action to start a new chat.
 */

import React from 'react';
import { Button } from '../ui/button';
import { Sparkles, MessageSquare, Plus } from 'lucide-react';

interface ChatEmptyStateProps {
  projectName: string;
  onNewChat: () => void;
}

export const ChatEmptyState: React.FC<ChatEmptyStateProps> = ({
  projectName,
  onNewChat,
}) => {
  return (
    <div className="flex flex-col h-full bg-background">
      <div className="border-b px-6 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Chat with {projectName}</h2>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No chats yet</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Start a conversation to explore your project sources
          </p>
          <Button onClick={onNewChat} className="gap-2">
            <Plus className="h-4 w-4" />
            Start New Chat
          </Button>
        </div>
      </div>
    </div>
  );
};
