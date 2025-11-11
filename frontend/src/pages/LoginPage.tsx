import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import Button from '../components/ui/Button';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuthStore();

  useEffect(() => {
    // If already authenticated, redirect to home
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = () => {
    login(); // This will redirect to Keycloak login page
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img src="/icon.png" alt="CrewUp logo" className="mx-auto h-16 w-16 mb-4 rounded-md" />
          <h1 className="text-4xl font-bold text-gray-900 mb-2">CrewUp 🚀</h1>
          <p className="text-gray-600">Find your crew for tonight's events</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Sign In</h2>
          
          <div className="space-y-4">
            <p className="text-gray-600 text-center mb-6">
              Click below to sign in with Keycloak
            </p>

            <Button
              onClick={handleLogin}
              variant="primary"
              className="w-full"
            >
              Sign In with Keycloak
            </Button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              New users will be automatically registered on first login
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
