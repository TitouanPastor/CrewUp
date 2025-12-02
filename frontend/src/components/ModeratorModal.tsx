import { useState } from 'react';
import { Shield, Search, Ban, UserCheck, Loader2, AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { moderationService } from '@/services/moderationService';

interface ModeratorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface SearchedUser {
  id: string;
  keycloak_id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_banned: boolean;
  is_active: boolean;
}

export default function ModeratorModal({ open, onOpenChange }: ModeratorModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchedUser[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedUser, setSelectedUser] = useState<SearchedUser | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [actionType, setActionType] = useState<'ban' | 'unban'>('ban');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast({
        title: 'Empty search',
        description: 'Please enter a name or email to search',
        variant: 'destructive',
      });
      return;
    }

    setIsSearching(true);
    try {
      const result = await moderationService.searchUsers(searchQuery);
      setSearchResults(result.users);

      if (result.users.length === 0) {
        toast({
          title: 'No results',
          description: 'No users found matching your search',
        });
      }
    } catch (error: any) {
      toast({
        title: 'Search failed',
        description: error.response?.data?.detail || 'Failed to search users',
        variant: 'destructive',
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleActionClick = (user: SearchedUser, action: 'ban' | 'unban') => {
    setSelectedUser(user);
    setActionType(action);
    setReason('');
    setShowConfirmDialog(true);
  };

  const handleConfirmAction = async () => {
    if (!selectedUser) return;

    if (reason.trim().length < 10) {
      toast({
        title: 'Reason required',
        description: 'Please provide a reason (at least 10 characters)',
        variant: 'destructive',
      });
      return;
    }

    if (reason.trim().length > 255) {
      toast({
        title: 'Reason too long',
        description: 'Reason must be no more than 255 characters',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await moderationService.banUser({
        user_keycloak_id: selectedUser.keycloak_id,
        ban: actionType === 'ban',
        reason: reason.trim(),
      });

      toast({
        title: 'Success',
        description: response.message,
      });

      // Update the user in search results
      setSearchResults(prev =>
        prev.map(u =>
          u.keycloak_id === selectedUser.keycloak_id
            ? { ...u, is_banned: actionType === 'ban' }
            : u
        )
      );

      setShowConfirmDialog(false);
      setSelectedUser(null);
      setReason('');
    } catch (error: any) {
      toast({
        title: 'Action failed',
        description: error.response?.data?.detail || `Failed to ${actionType} user`,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-primary" />
              <DialogTitle>Moderator Panel</DialogTitle>
            </div>
            <DialogDescription>
              Search and manage user access to the platform
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Search Section */}
            <div className="space-y-3">
              <Label htmlFor="search">Search Users</Label>
              <div className="flex gap-2">
                <Input
                  id="search"
                  placeholder="Search by name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  disabled={isSearching}
                />
                <Button
                  onClick={handleSearch}
                  disabled={isSearching}
                  size="icon"
                >
                  {isSearching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-3">
                <Label>Search Results ({searchResults.length})</Label>
                <div className="border rounded-lg divide-y max-h-[400px] overflow-y-auto">
                  {searchResults.map((user) => (
                    <div
                      key={user.id}
                      className="p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium truncate">
                              {user.first_name} {user.last_name}
                            </p>
                            {user.is_banned && (
                              <Badge variant="destructive" className="flex items-center gap-1">
                                <Ban className="h-3 w-3" />
                                Banned
                              </Badge>
                            )}
                            {!user.is_active && (
                              <Badge variant="secondary">Inactive</Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground truncate">
                            {user.email}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {user.is_banned ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleActionClick(user, 'unban')}
                              className="flex items-center gap-1"
                            >
                              <UserCheck className="h-4 w-4" />
                              Unban
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleActionClick(user, 'ban')}
                              className="flex items-center gap-1"
                            >
                              <Ban className="h-4 w-4" />
                              Ban
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {searchResults.length === 0 && !isSearching && (
              <div className="py-8 text-center">
                <Shield className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">User Management</h3>
                <p className="text-muted-foreground text-sm">
                  Search for users by name or email to manage their access
                </p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <AlertDialogTitle>
                Confirm {actionType === 'ban' ? 'Ban' : 'Unban'} User
              </AlertDialogTitle>
            </div>
            <AlertDialogDescription asChild>
              <div className="space-y-4">
                <p>
                  Are you sure you want to {actionType}{' '}
                  <span className="font-semibold">
                    {selectedUser?.first_name} {selectedUser?.last_name}
                  </span>{' '}
                  ({selectedUser?.email})?
                </p>
                <div className="space-y-2">
                  <Label htmlFor="reason">
                    Reason <span className="text-destructive">*</span>
                  </Label>
                  <Textarea
                    id="reason"
                    placeholder={`Provide a reason for ${actionType}ning this user (10-255 characters)...`}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    rows={3}
                    maxLength={255}
                    disabled={isSubmitting}
                  />
                  <p className="text-xs text-muted-foreground">
                    {reason.length}/255 characters
                    {reason.length < 10 && reason.length > 0 && (
                      <span className="text-destructive ml-2">
                        (Minimum 10 characters required)
                      </span>
                    )}
                  </p>
                </div>
                {actionType === 'ban' && (
                  <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                    ⚠️ Banning will prevent this user from accessing the platform.
                  </p>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isSubmitting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmAction}
              disabled={isSubmitting || reason.trim().length < 10}
              className={actionType === 'ban' ? 'bg-destructive hover:bg-destructive/90' : ''}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>Confirm {actionType === 'ban' ? 'Ban' : 'Unban'}</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
