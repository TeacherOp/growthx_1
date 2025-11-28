/**
 * StudioToolItem Component
 * Educational Note: Compact tool button for the Studio panel.
 * Shows icon and name only for a cleaner, space-efficient layout.
 */

import React from 'react';
import { Button } from '../ui/button';
import type { GenerationOption } from './types';

interface StudioToolItemProps {
  option: GenerationOption;
  onClick: (optionId: string) => void;
}

export const StudioToolItem: React.FC<StudioToolItemProps> = ({ option, onClick }) => {
  const Icon = option.icon;

  return (
    <Button
      variant="outline"
      className="h-auto px-3 py-2 justify-start text-left hover:bg-accent"
      onClick={() => onClick(option.id)}
    >
      <Icon size={16} className="text-primary mr-2 flex-shrink-0" />
      <span className="text-sm">{option.title}</span>
    </Button>
  );
};
