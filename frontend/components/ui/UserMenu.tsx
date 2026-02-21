'use client';

import { ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { UI_CONSTANTS, USER_MENU_ACTIONS } from '../../constants';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './dropdown-menu';

interface UserMenuProps {
  user: { id: string; name?: string; role?: string } | null;
  isOpen?: boolean; // Kept for compatibility but not strictly needed for Radix
  onToggle?: () => void; // Kept for compatibility
  onClose?: () => void; // Kept for compatibility
}

export function UserMenu({ user }: UserMenuProps) {
  const router = useRouter();

  const handleMenuAction = (action: string) => {
    if (action === USER_MENU_ACTIONS.SETTINGS) {
      router.push('/settings');
      return;
    }
    console.log(`User action: ${action}`);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger suppressHydrationWarning className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 data-[state=open]:bg-gray-50 outline-none">
        {/* Avatar */}
        <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-medium">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </span>
        </div>

        {/* User Info */}
        <div className="flex flex-col items-start text-left">
          <span className="text-sm font-medium text-gray-900">
            {user?.name || 'Loading…'}
          </span>
          <span className="text-xs text-gray-500 capitalize">
            {user?.role || 'User'}
          </span>
        </div>

        {/* Dropdown Arrow */}
        <ChevronDown
          className="w-4 h-4 text-gray-500 transition-transform duration-200 group-data-[state=open]:rotate-180"
        />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56 bg-white">
        {/* User Info Header as Label */}
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user?.name || 'Loading...'}</p>
            <p className="text-xs leading-none text-muted-foreground">{user?.role || 'User'}</p>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem onClick={() => handleMenuAction(USER_MENU_ACTIONS.SETTINGS)} className="cursor-pointer">
          Settings
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => handleMenuAction(USER_MENU_ACTIONS.LOGOUT)}
          className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50"
        >
          {UI_CONSTANTS.BUTTONS.SIGN_OUT}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

