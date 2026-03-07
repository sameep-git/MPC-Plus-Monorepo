'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signIn } from '../../lib/auth';
import { Button, Input, Label, Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../components/ui';
import { AlertCircle } from 'lucide-react';

export default function SignInPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await signIn(username, password);
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 transition-colors">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <div className="text-3xl font-bold text-purple-900 dark:text-purple-400 font-fraunces">
            MPC Plus
          </div>
          <CardTitle>Sign In</CardTitle>
          <p className="text-sm text-muted-foreground">
            Enter your credentials to access the dashboard
          </p>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSignIn} className="space-y-4">
            {error && (
              <div className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-xs text-blue-600 dark:text-blue-400">
              <strong>Demo Admin:</strong> username: <code className="font-mono">admin</code>, password: <code className="font-mono">admin123</code>
            </p>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-2 text-sm text-center text-muted-foreground">
          <p>Don't have an account?</p>
          <Link
            href="/signup"
            className="text-primary hover:underline font-medium"
          >
            Create an account
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
