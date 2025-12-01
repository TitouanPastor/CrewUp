import { Shield } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ModeratorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function ModeratorModal({ open, onOpenChange }: ModeratorModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" />
            <DialogTitle>Moderator Panel</DialogTitle>
          </div>
          <DialogDescription>
            Content moderation and management tools
          </DialogDescription>
        </DialogHeader>

        <div className="py-8 text-center">
          <Shield className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">Moderator Tools</h3>
          <p className="text-muted-foreground">
            Moderation features will be available here.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            This is a placeholder for future moderation functionality.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
