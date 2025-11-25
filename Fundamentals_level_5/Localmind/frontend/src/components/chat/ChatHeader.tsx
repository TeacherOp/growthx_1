/**
 * ChatHeader Component
 * Educational Note: Header with chat title dropdown and new chat button.
 * Allows quick switching between chats via dropdown menu.
 */

import React from 'react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { Sparkles, Plus, MessageSquare, ChevronDown, Hash } from 'lucide-react';
import type { Chat, ChatMetadata } from '../../lib/api/chats';

interface ChatHeaderProps {
  activeChat: Chat | null;
  allChats: ChatMetadata[];
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onShowChatList: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  activeChat,
  allChats,
  onSelectChat,
  onNewChat,
  onShowChatList,
}) => {
  return (
    <div className="border-b px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-auto p-1 gap-2">
                <span className="font-semibold">{activeChat?.title || 'Chat'}</span>
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuItem onClick={onShowChatList}>
                <MessageSquare className="h-4 w-4 mr-2" />
                View All Chats
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {allChats.slice(0, 5).map((chat) => (
                <DropdownMenuItem
                  key={chat.id}
                  onClick={() => onSelectChat(chat.id)}
                  className={chat.id === activeChat?.id ? 'bg-accent' : ''}
                >
                  <Hash className="h-4 w-4 mr-2" />
                  {chat.title}
                </DropdownMenuItem>
              ))}
              {allChats.length > 5 && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={onShowChatList}>
                    View more...
                  </DropdownMenuItem>
                </>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onNewChat}>
                <Plus className="h-4 w-4 mr-2" />
                New Chat
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <Button variant="outline" size="sm" onClick={onNewChat}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        Ask questions about your sources or request analysis
      </p>
    </div>
  );
};
