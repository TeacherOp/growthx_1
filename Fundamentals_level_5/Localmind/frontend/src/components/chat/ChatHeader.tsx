/**
 * ChatHeader Component
 * Educational Note: Header with chat title dropdown and new chat button.
 * Allows quick switching between chats via dropdown menu.
 */

import React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { Sparkle, Plus, ChatCircle, CaretDown, Hash } from '@phosphor-icons/react';
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
    <div className="border-b px-4 py-3">
      {/* Title row - matches Sources/Studio/ChatEmptyState structure */}
      <div className="flex items-center gap-2">
        <Sparkle size={20} className="text-primary" />
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-1 hover:opacity-80 transition-opacity">
            <h2 className="font-semibold">{activeChat?.title || 'Chat'}</h2>
            <CaretDown size={14} className="text-muted-foreground" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuItem onClick={onShowChatList}>
              <ChatCircle size={16} className="mr-2" />
              View All Chats
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {allChats.slice(0, 5).map((chat) => (
              <DropdownMenuItem
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={chat.id === activeChat?.id ? 'bg-accent' : ''}
              >
                <Hash size={16} className="mr-2" />
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
              <Plus size={16} className="mr-2" />
              New Chat
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {/* Description - matches Sources/Studio */}
      <p className="text-xs text-muted-foreground mt-1">
        Ask questions about your sources or request analysis
      </p>
    </div>
  );
};
