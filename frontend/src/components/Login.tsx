import { useState } from 'react';
import { login } from '../services/api';
import { Zap } from 'lucide-react';

interface LoginProps {
  onLogin: (token: string) => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await login(username, password);
      onLogin(data.token);
    } catch (err) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-content">
        <div className="login-header">
          <div className="logo-container">
            <div className="logo">
              <svg className="logo-icon" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#a78bfa" />
                    <stop offset="100%" stopColor="#7c3aed" />
                  </linearGradient>
                </defs>
                {/* background circle */}
                <circle cx="50" cy="50" r="45" fill="url(#purpleGrad)" />
                {/* bars */}
                <rect x="20" y="50" width="8" height="25" fill="white" />
                <rect x="34" y="40" width="8" height="35" fill="white" />
                <rect x="48" y="30" width="8" height="45" fill="white" />
                <rect x="62" y="44" width="8" height="31" fill="white" />
                <rect x="76" y="54" width="8" height="21" fill="white" />
                {/* pulse line */}
                <path d="M15 60 L25 60 L30 50 L35 70 L40 45 L45 65 L50 55 L55 65 L60 50 L65 60 L75 60" stroke="white" strokeWidth="2" fill="none" />
              </svg>
            </div>
            <div className="logo-text">
              <div className="logo-title">
                <span className="logo-main">Risk</span>
                <span className="logo-accent">Pulse</span>
              </div>
              <div className="logo-subtitle">Intelligence Platform</div>
            </div>
          </div>
          <h1 className="main-title">Welcome Back</h1>
          <p className="subtitle">Sign in to access your Risk Pulse dashboard</p>
        </div>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
        
        <div className="login-footer">
          <p>Risk Pulse & Market Intelligence Platform</p>
        </div>
      </div>
    </div>
  );
}