/**
 * ChatPanel Component
 * Educational Note: Main orchestrator for the chat interface.
 * Composes smaller components (ChatHeader, ChatMessages, ChatInput, etc.)
 * and manages chat state and API interactions.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { chatsAPI } from '../lib/api/chats';
import type { Chat, ChatMetadata } from '../lib/api/chats';
import { useToast, ToastContainer } from './ui/toast';
import { useVoiceRecording } from './hooks/useVoiceRecording';
import {
  ChatHeader,
  ChatMessages,
  ChatInput,
  ChatList,
  ChatEmptyState,
} from './chat';

interface ChatPanelProps {
  projectId: string;
  projectName: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ projectId, projectName }) => {
  const { toasts, dismissToast, success, error } = useToast();

  // Chat state
  const [message, setMessage] = useState('');
  const [activeChat, setActiveChat] = useState<Chat | null>(null);
  const [showChatList, setShowChatList] = useState(false);
  const [allChats, setAllChats] = useState<ChatMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  // Voice recording hook
  const {
    isRecording,
    partialTranscript,
    transcriptionConfigured,
    startRecording,
    stopRecording,
  } = useVoiceRecording({
    onError: error,
    onTranscriptCommit: useCallback((text: string) => {
      // Append committed text to message
      setMessage((prev) => {
        if (prev && !prev.endsWith(' ')) {
          return prev + ' ' + text;
        }
        return prev + text;
      });
    }, []),
  });

  /**
   * Load all chats when component mounts or projectId changes
   */
  useEffect(() => {
    loadChats();
  }, [projectId]);

  /**
   * Load all chats for the project
   */
  const loadChats = async () => {
    try {
      setLoading(true);
      const chats = await chatsAPI.listChats(projectId);
      setAllChats(chats);

      // If we have chats and no active chat, load the first one
      if (chats.length > 0 && !activeChat) {
        await loadFullChat(chats[0].id);
      }
    } catch (err) {
      console.error('Error loading chats:', err);
      error('Failed to load chats');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load full chat data including all messages
   */
  const loadFullChat = async (chatId: string) => {
    try {
      const chat = await chatsAPI.getChat(projectId, chatId);
      setActiveChat(chat);
    } catch (err) {
      console.error('Error loading chat:', err);
      error('Failed to load chat');
    }
  };

  /**
   * Send a message and get AI response
   */
  const handleSend = async () => {
    if (!message.trim() || !activeChat || sending) return;

    const userMessage = message.trim();
    setMessage('');
    setSending(true);

    try {
      const result = await chatsAPI.sendMessage(projectId, activeChat.id, userMessage);

      // Update the active chat with new messages
      setActiveChat((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: [...prev.messages, result.user_message, result.assistant_message],
          updated_at: new Date().toISOString(),
        };
      });

      // Update the chat metadata in the list
      await loadChats();
    } catch (err) {
      console.error('Error sending message:', err);
      error('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  /**
   * Create a new chat
   */
  const handleNewChat = async () => {
    try {
      const newChat = await chatsAPI.createChat(projectId, 'New Chat');
      await loadChats();
      await loadFullChat(newChat.id);
      setShowChatList(false);
      success('New chat created');
    } catch (err) {
      console.error('Error creating chat:', err);
      error('Failed to create chat');
    }
  };

  /**
   * Select a chat from the list
   */
  const handleSelectChat = async (chatId: string) => {
    await loadFullChat(chatId);
    setShowChatList(false);
  };

  /**
   * Delete a chat
   */
  const handleDeleteChat = async (chatId: string) => {
    try {
      await chatsAPI.deleteChat(projectId, chatId);

      // If the deleted chat was active, clear it
      if (activeChat?.id === chatId) {
        setActiveChat(null);
      }

      await loadChats();
      success('Chat deleted');
    } catch (err) {
      console.error('Error deleting chat:', err);
      error('Failed to delete chat');
    }
  };

  /**
   * Toggle recording on/off
   */
  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Loading state
  if (loading) {
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
            <Loader2 className="h-8 w-8 mx-auto mb-4 text-muted-foreground animate-spin" />
            <p className="text-sm text-muted-foreground">Loading chats...</p>
          </div>
        </div>
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </div>
    );
  }

  // Empty state - no chats exist
  if (allChats.length === 0 && !activeChat) {
    return (
      <>
        <ChatEmptyState projectName={projectName} onNewChat={handleNewChat} />
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </>
    );
  }

  // Chat list view
  if (showChatList) {
    return (
      <>
        <ChatList
          chats={allChats}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          onNewChat={handleNewChat}
        />
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </>
    );
  }

  // Active chat view
  return (
    <div className="flex flex-col h-full bg-background">
      <ChatHeader
        activeChat={activeChat}
        allChats={allChats}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onShowChatList={() => setShowChatList(true)}
      />

      <ChatMessages messages={activeChat?.messages || []} sending={sending} />

      <ChatInput
        message={message}
        partialTranscript={partialTranscript}
        isRecording={isRecording}
        sending={sending}
        transcriptionConfigured={transcriptionConfigured}
        onMessageChange={setMessage}
        onSend={handleSend}
        onMicClick={handleMicClick}
      />

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};
