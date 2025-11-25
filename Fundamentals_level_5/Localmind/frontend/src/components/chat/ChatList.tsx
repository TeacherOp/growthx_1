/**
 * ChatList Component
 * Educational Note: Displays all chats for a project with ability to
 * select, delete, or create new chats. Shows chat metadata like
 * message count and last updated time.
 */

import React from 'react';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Sparkles, Plus, Clock, Hash, Trash2 } from 'lucide-react';
import type { ChatMetadata } from '../../lib/api/chats';

interface ChatListProps {
  chats: ChatMetadata[];
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onNewChat: () => void;
}

/**
 * Helper function to format relative time
 */
const formatRelativeTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};

export const ChatList: React.FC<ChatListProps> = ({
  chats,
  onSelectChat,
  onDeleteChat,
  onNewChat,
}) => {
  return (
    <div className="flex flex-col h-full bg-background">
      <div className="border-b px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">All Chats</h2>
          </div>
          <Button size="sm" onClick={onNewChat} className="gap-2">
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className="p-3 border rounded-lg hover:bg-accent transition-colors group"
            >
              <div className="flex items-start justify-between mb-1">
                <div
                  className="flex-1 cursor-pointer"
                  onClick={() => onSelectChat(chat.id)}
                >
                  <div className="flex items-center gap-2">
                    <Hash className="h-4 w-4 text-muted-foreground" />
                    <h3 className="font-medium text-sm">{chat.title}</h3>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatRelativeTime(chat.updated_at)}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteChat(chat.id);
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </div>
              </div>
              <p
                className="text-xs text-muted-foreground line-clamp-2 cursor-pointer"
                onClick={() => onSelectChat(chat.id)}
              >
                {chat.message_count} messages
              </p>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};
