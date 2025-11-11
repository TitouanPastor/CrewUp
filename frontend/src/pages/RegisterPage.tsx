import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import Button from '../components/ui/Button';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleRegister = () => {
    login();
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
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Account</h2>
          
          <div className="space-y-4">
            <p className="text-gray-600 text-center mb-6">
              Create your CrewUp account through Keycloak
            </p>

            <Button
              onClick={handleRegister}
              variant="primary"
              className="w-full"
            >
              Register with Keycloak
            </Button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="text-primary-600 hover:text-primary-700 font-semibold">
                Sign In
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
