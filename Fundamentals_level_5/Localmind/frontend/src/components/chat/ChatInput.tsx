/**
 * ChatInput Component
 * Educational Note: Input area with microphone button for voice input,
 * text field for typing, and send button. Displays partial transcripts
 * in real-time while recording.
 */

import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Send, Mic, Loader2 } from 'lucide-react';

interface ChatInputProps {
  message: string;
  partialTranscript: string;
  isRecording: boolean;
  sending: boolean;
  transcriptionConfigured: boolean;
  onMessageChange: (value: string) => void;
  onSend: () => void;
  onMicClick: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  message,
  partialTranscript,
  isRecording,
  sending,
  transcriptionConfigured,
  onMessageChange,
  onSend,
  onMicClick,
}) => {
  // Display value combines typed message and partial transcript
  const displayMessage = partialTranscript
    ? message + (message && !message.endsWith(' ') ? ' ' : '') + partialTranscript
    : message;

  return (
    <div className="border-t p-4">
      <div className="flex gap-2">
        {/* Microphone Button - Click to toggle recording */}
        <Button
          variant={isRecording ? 'default' : 'outline'}
          size="icon"
          className={`h-10 w-10 flex-shrink-0 ${
            isRecording ? 'bg-red-500 hover:bg-red-600 animate-pulse' : ''
          } ${!transcriptionConfigured ? 'opacity-50' : ''}`}
          onClick={onMicClick}
          disabled={sending || !transcriptionConfigured}
          title={
            !transcriptionConfigured
              ? 'Set up ElevenLabs API key in settings'
              : isRecording
              ? 'Click to stop recording'
              : 'Click to start recording'
          }
        >
          <Mic className={`h-4 w-4 ${isRecording ? 'text-white' : ''}`} />
        </Button>

        <div className="flex-1 relative">
          <Input
            placeholder={
              isRecording
                ? 'Listening...'
                : !transcriptionConfigured
                ? 'Type your message... (voice disabled - set API key)'
                : 'Ask about your sources...'
            }
            value={displayMessage}
            onChange={(e) => onMessageChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && !isRecording && onSend()}
            className={`pr-10 ${partialTranscript ? 'text-muted-foreground' : ''}`}
            disabled={sending || isRecording}
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={onSend}
            className="absolute right-1 top-1 h-7 w-7"
            disabled={!message.trim() || sending || isRecording}
          >
            {sending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground mt-2 text-center">
        {isRecording
          ? 'Listening... Click mic to stop'
          : !transcriptionConfigured
          ? 'Voice input requires ElevenLabs API key (App Settings)'
          : 'Click mic to speak, or type your message'}
      </p>
    </div>
  );
};
