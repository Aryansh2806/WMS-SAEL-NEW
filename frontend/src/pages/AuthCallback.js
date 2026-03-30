import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Package, Loader2 } from 'lucide-react';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { processGoogleAuth, setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Use useRef to prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Get session_id from URL hash
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.replace('#', ''));
        const sessionId = params.get('session_id');

        if (!sessionId) {
          console.error('No session_id found in URL');
          navigate('/login');
          return;
        }

        // Exchange session_id for session
        const result = await processGoogleAuth(sessionId);
        
        if (result?.user) {
          setUser(result.user);
          // Clear the hash from URL and navigate
          window.history.replaceState(null, '', '/dashboard');
          navigate('/dashboard', { replace: true, state: { user: result.user } });
        } else {
          navigate('/login');
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/login');
      }
    };

    processAuth();
  }, [navigate, processGoogleAuth, setUser]);

  return (
    <div 
      className="min-h-screen flex items-center justify-center"
      style={{
        backgroundImage: `linear-gradient(rgba(26, 39, 68, 0.85), rgba(26, 39, 68, 0.9)), url('https://images.pexels.com/photos/221047/pexels-photo-221047.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}
    >
      <div className="bg-white rounded-xl p-8 shadow-2xl text-center">
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-[#f59e0b] rounded-xl flex items-center justify-center">
            <Package className="w-10 h-10 text-white" />
          </div>
        </div>
        <div className="flex items-center justify-center gap-2 text-gray-600">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Completing sign in...</span>
        </div>
      </div>
    </div>
  );
};

export default AuthCallback;
