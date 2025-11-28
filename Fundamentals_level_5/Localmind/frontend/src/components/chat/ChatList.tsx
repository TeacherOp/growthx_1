/**
 * ChatList Component
 * Educational Note: Displays all chats for a project with ability to
 * select, delete, or create new chats. Shows chat metadata like
 * message count and last updated time.
 */

import React from 'react';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Sparkle, Plus, Clock, Hash, Trash } from '@phosphor-icons/react';
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
    <div className="flex flex-col h-full bg-card">
      {/* Header - matches Sources/Studio/ChatEmptyState structure */}
      <div className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkle size={20} className="text-primary" />
          <h2 className="font-semibold">All Chats</h2>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Select a chat to continue or start a new one
        </p>
      </div>

      {/* New Chat Button - in controls section */}
      <div className="px-4 pt-4">
        <Button onClick={onNewChat} variant="outline" className="w-full gap-2">
          <Plus size={16} />
          New Chat
        </Button>
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
                    <Hash size={16} className="text-muted-foreground" />
                    <h3 className="font-medium text-sm">{chat.title}</h3>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock size={12} />
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
                    <Trash size={14} className="text-destructive" />
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
