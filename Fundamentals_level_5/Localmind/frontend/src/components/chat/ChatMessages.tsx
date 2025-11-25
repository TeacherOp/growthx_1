/**
 * ChatMessages Component
 * Educational Note: Displays the conversation message list with user and AI messages.
 * Shows a loading indicator when waiting for AI response.
 */

import React from 'react';
import { ScrollArea } from '../ui/scroll-area';
import { User, Bot, Loader2 } from 'lucide-react';
import type { Message } from '../../lib/api/chats';

interface ChatMessagesProps {
  messages: Message[];
  sending: boolean;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, sending }) => {
  return (
    <ScrollArea className="flex-1 px-6">
      <div className="py-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className="flex gap-3">
            <div className="flex-shrink-0">
              {msg.role === 'user' ? (
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-4 w-4" />
                </div>
              ) : (
                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
            </div>
            <div className="flex-1 space-y-1">
              <p className="text-xs font-medium text-muted-foreground">
                {msg.role === 'user' ? 'You' : 'LocalMind'}
              </p>
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              {msg.error && (
                <p className="text-xs text-destructive">This message had an error</p>
              )}
            </div>
          </div>
        ))}

        {/* Show loading indicator when sending */}
        {sending && (
          <div className="flex gap-3">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
            </div>
            <div className="flex-1 space-y-1">
              <p className="text-xs font-medium text-muted-foreground">LocalLm</p>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Thinking...
              </div>
            </div>
          </div>
        )}
      </div>
    </ScrollArea>
  );
};
