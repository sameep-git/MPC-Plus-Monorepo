'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { fetchMachines, fetchUpdates, fetchUser, handleApiError } from '../lib/api';
import type { Machine as MachineType } from '../models/Machine';
import type { UpdateModel as UpdateModelType } from '../models/Update';
import { Navbar, Button } from '../components/ui';
import { UpdateCard } from '../components/dashboard/UpdateCard';
import { UI_CONSTANTS, NAVIGATION } from '../constants';

export default function Home() {
  const router = useRouter();
  const [machines, setMachines] = useState<MachineType[]>([]);
  const [machinesLoading, setMachinesLoading] = useState(true);
  const [machinesError, setMachinesError] = useState<string | null>(null);

  const [updates, setUpdates] = useState<UpdateModelType[]>([]);
  const [updatesLoading, setUpdatesLoading] = useState(true);
  const [updatesError, setUpdatesError] = useState<string | null>(null);

  const [user, setUser] = useState<{ id: string; name?: string; role?: string } | null>(null);

  const handleMachineSelect = (machineId: string, e: React.MouseEvent) => {
    e.preventDefault();
    // Store the selected machine ID in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('selectedMachineId', machineId);
      // Navigate to the results page
      router.push(NAVIGATION.ROUTES.MPC_RESULT);
    }
  };

  const handleViewAllResults = (e: React.MouseEvent) => {
    e.preventDefault();
    // If there are machines, select the first one by default
    if (machines.length > 0) {
      if (typeof window !== 'undefined') {
        localStorage.setItem('selectedMachineId', machines[0].id);
      }
    }
    // Navigate to the results page
    router.push(NAVIGATION.ROUTES.MPC_RESULT);
  };

  useEffect(() => {
    fetchMachines()
      .then((data) => setMachines(data))
      .catch((err) => setMachinesError(handleApiError(err)))
      .finally(() => setMachinesLoading(false));
    fetchUpdates()
      .then((data) => setUpdates(data))
      .catch((err) => setUpdatesError(handleApiError(err)))
      .finally(() => setUpdatesLoading(false));
    fetchUser()
      .then((data) => setUser(data))
      .catch((err) => console.error(handleApiError(err))); // Log error but don't set state
  }, []);

  return (
    <div className="min-h-screen bg-background transition-colors">
      {/* Header */}
      <Navbar user={user} />

      <main className="p-6 max-w-6xl mx-auto">
        {/* Welcome Section */}
        <section className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            {UI_CONSTANTS.TITLES.WELCOME}, {user?.name || UI_CONSTANTS.STATUS.USER}!
          </h1>
          <p className="text-muted-foreground mb-6 max-w-2xl">
            Monitor and manage your machine performance checks. View results, track updates, and access detailed analytics for your equipment.
          </p>
          <Button
            size="lg"
            onClick={handleViewAllResults}
          >
            {UI_CONSTANTS.BUTTONS.VIEW_ALL_RESULTS}
          </Button>
        </section>

        {/* Error Display for Machines */}
        {machinesError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{UI_CONSTANTS.ERRORS.LOADING_DATA} {machinesError}</p>
            <Button
              onClick={() => window.location.reload()}
              variant="ghost"
              className="mt-2 text-red-600 hover:text-red-800"
            >
              {UI_CONSTANTS.BUTTONS.RETRY}
            </Button>
          </div>
        )}

        {/* Today's Machine Updates */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-foreground mb-6">{UI_CONSTANTS.TITLES.TODAYS_UPDATES}</h2>
          <div className="flex flex-wrap gap-4">
            {machinesLoading ? (
              // Loading skeleton
              Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="bg-gray-200 animate-pulse h-12 w-48 rounded-lg"></div>
              ))
            ) : machines.length === 0 ? (
              <div className="text-gray-500 italic">{UI_CONSTANTS.ERRORS.NO_MACHINES}</div>
            ) : (
              machines.map((machine) => {
                const handleMachineClick = (e: React.MouseEvent) => {
                  handleMachineSelect(machine.id, e);
                };
                return (
                  <Link
                    key={machine.id}
                    href={NAVIGATION.ROUTES.MPC_RESULT}
                    onClick={handleMachineClick}
                    className="bg-primary text-primary-foreground px-6 py-3 rounded-xl font-medium hover:bg-primary/90 transition-colors min-w-[200px] relative inline-block text-center shadow-sm"
                    title={`${machine.name}${machine.location ? ` | Location: ${machine.location}` : ''}${machine.type ? ` | Type: ${machine.type}` : ''}`}
                  >
                    <div className="font-bold">{machine.name}</div>
                    {machine.location && (
                      <div className="text-xs text-primary-foreground/80">{machine.location}</div>
                    )}
                    {machine.type && (
                      <div className="text-xs text-primary-foreground/70">{machine.type}</div>
                    )}
                  </Link>
                );
              })
            )}
          </div>
        </section>

        {/* Divider */}
        <div className="border-t border-gray-200 my-8"></div>

        {/* Latest Updates */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h2 className="text-3xl font-bold text-foreground mb-4">{UI_CONSTANTS.TITLES.LATEST_UPDATES}</h2>
            <Button size="lg">
              {UI_CONSTANTS.BUTTONS.VIEW_ALL_UPDATES}
            </Button>
          </div>

          <div className="space-y-4">
            {updatesError && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600">{UI_CONSTANTS.ERRORS.LOADING_DATA} {updatesError}</p>
              </div>
            )}
            {updatesLoading ? (
              // Loading skeleton for updates
              Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="bg-gray-100 animate-pulse h-20 rounded-lg"></div>
              ))
            ) : (
              updates.map((update) => (
                <UpdateCard
                  key={update.id}
                  machineId={update.machineId}
                  description={update.info ?? ''}
                  iconType={(update.type as keyof typeof UI_CONSTANTS.UPDATE_ICON_TYPE) || 'INFO'}
                  onClick={() => {/* Handle click event */ }}
                />
              ))
            )}
          </div>
        </section>

        {/* Additional Information */}
        <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-muted-foreground text-sm">
            Stay informed about important changes, threshold alerts, and system updates. Click on any update card above to view more details.
          </p>
        </div>
      </main>
    </div>
  );
}
