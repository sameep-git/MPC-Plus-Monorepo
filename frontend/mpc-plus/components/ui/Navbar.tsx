'use client';

import { useState } from 'react';
import Link from 'next/link';
import { UserMenu } from './UserMenu';
import { NAVIGATION } from '../../constants';

interface NavbarProps {
  user: { id: string; name?: string } | null;
}

export function Navbar({ user }: NavbarProps) {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  return (
    <header className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 transition-colors">
      {/* Logo/Brand */}
      <Link href={NAVIGATION.ROUTES.HOME} className="text-2xl font-bold text-purple-900 dark:text-purple-400 font-fraunces hover:text-purple-700 dark:hover:text-purple-300 transition-colors">
        MPC Plus
      </Link>

      {/* Navigation Links */}
      <nav className="hidden md:flex items-center space-x-8">
        <Link href={NAVIGATION.ROUTES.HOME} className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors">
          Dashboard
        </Link>
        <Link href={NAVIGATION.ROUTES.MPC_RESULT} className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors">
          Machines
        </Link>
        <Link href={NAVIGATION.ROUTES.SETTINGS} className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors">
          Settings
        </Link>
      </nav>

      {/* User Menu */}
      <UserMenu
        user={user}
        isOpen={isUserMenuOpen}
        onToggle={() => setIsUserMenuOpen(!isUserMenuOpen)}
        onClose={() => setIsUserMenuOpen(false)}
      />
    </header>
  );
}
