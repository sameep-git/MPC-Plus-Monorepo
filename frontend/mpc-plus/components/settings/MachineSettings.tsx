'use client';

import { useState, useEffect } from 'react';
import { Edit2, Loader2, Save, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    DialogDescription,
} from '../ui/dialog';
import { fetchMachines, updateMachine } from '../../lib/api';
import type { Machine } from '../../models/Machine';

export default function MachineSettings() {
    const [machines, setMachines] = useState<Machine[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Edit state
    const [editingMachine, setEditingMachine] = useState<Machine | null>(null);
    const [isEditOpen, setIsEditOpen] = useState(false);
    const [saving, setSaving] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        location: '',
    });

    const loadMachines = async () => {
        try {
            setLoading(true);
            const data = await fetchMachines();
            setMachines(data);
            setError(null);
        } catch (err) {
            console.error('Failed to load machines:', err);
            setError('Failed to load machines. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMachines();
    }, []);

    const handleEditClick = (machine: Machine) => {
        setEditingMachine(machine);
        setFormData({
            name: machine.name,
            location: machine.location || '',
        });
        setIsEditOpen(true);
        setError(null);
        setSuccess(null);
    };

    const handleSave = async () => {
        if (!editingMachine) return;

        try {
            setSaving(true);
            setError(null);

            const updatedMachine: Machine = {
                ...editingMachine,
                name: formData.name,
                location: formData.location,
            };

            await updateMachine(updatedMachine);

            setSuccess('Machine updated successfully');
            setIsEditOpen(false);
            loadMachines(); // Refresh list

            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            console.error('Failed to update machine:', err);
            setError('Failed to update machine. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    if (loading && machines.length === 0) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-3 text-lg text-gray-500">Loading machines...</span>
            </div>
        );
    }

    return (
        <section className="space-y-6">
            <div className="flex flex-col gap-2">
                <h2 className="text-2xl font-bold tracking-tight">Machine Management</h2>
                <p className="text-muted-foreground">
                    View and update machine details including name and location.
                </p>
            </div>

            {error && (
                <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-lg flex items-center gap-2">
                    <X className="w-4 h-4" />
                    {error}
                </div>
            )}

            {success && (
                <div className="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-4 rounded-lg flex items-center gap-2">
                    <Save className="w-4 h-4" />
                    {success}
                </div>
            )}

            <div className="rounded-md border">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b bg-muted/50 transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                            <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Name</th>
                            <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Location</th>
                            <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Type</th>
                            <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">ID</th>
                            <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {machines.map((machine) => (
                            <tr key={machine.id} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                <td className="p-4 align-middle font-medium">{machine.name}</td>
                                <td className="p-4 align-middle">{machine.location || '-'}</td>
                                <td className="p-4 align-middle">{machine.type || '-'}</td>
                                <td className="p-4 align-middle font-mono text-xs text-muted-foreground">{machine.id}</td>
                                <td className="p-4 align-middle text-right">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleEditClick(machine)}
                                        className="h-8 w-8 p-0"
                                    >
                                        <Edit2 className="h-4 w-4" />
                                        <span className="sr-only">Edit</span>
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Edit Machine</DialogTitle>
                        <DialogDescription>
                            Update the details for {editingMachine?.name}.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="location">Location</Label>
                            <Input
                                id="location"
                                value={formData.location}
                                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                placeholder="e.g. Room 101"
                            />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsEditOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save Changes
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </section>
    );
}
