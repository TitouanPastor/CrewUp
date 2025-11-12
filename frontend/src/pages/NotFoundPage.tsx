import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[100dvh] flex items-center justify-center p-4 bg-background">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 text-center space-y-6">
          <div className="space-y-2">
            <h1 className="text-9xl font-bold text-primary">404</h1>
            <h2 className="text-2xl font-semibold text-foreground">Page not found</h2>
            <p className="text-muted-foreground">
              The page you're looking for doesn't exist or has been moved.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button
              onClick={() => navigate(-1)}
              variant="outline"
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Go Back
            </Button>
            <Button
              onClick={() => navigate('/')}
              className="gap-2"
            >
              <Home className="h-4 w-4" />
              Home Page
            </Button>
          </div>

          <div className="pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              Lost? Check out our <a href="/" className="text-primary hover:underline">homepage</a> or{' '}
              <a href="/events" className="text-primary hover:underline">browse events</a>.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
