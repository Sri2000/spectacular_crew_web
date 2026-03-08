import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, Upload, TrendingUp, Activity, ChevronRight, Zap, ArrowLeftRight, Building2, LogOut, Play } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
  onLogout: () => void;
}

export default function Layout({ children, onLogout }: LayoutProps) {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Analyst Dashboard', icon: BarChart3, description: 'Risk monitoring' },
    { path: '/executive', label: 'Executive View', icon: TrendingUp, description: 'Decision support' },
    { path: '/transfers', label: 'Stock Transfer', icon: ArrowLeftRight, description: 'Rebalance stores' },
    { path: '/dashboard', label: 'Fleet Dashboard', icon: Building2, description: 'Enterprise view' },
    { path: '/simulate', label: 'Simulate', icon: Play, description: 'Run scenarios' },
    { path: '/upload', label: 'Data Upload', icon: Upload, description: 'Upload datasets' },
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 flex flex-col flex-shrink-0" style={{ background: 'linear-gradient(180deg, #0a0f1e 0%, #0f172a 50%, #111827 100%)' }}>
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/5">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #6366f1, #7c3aed)', boxShadow: '0 4px 14px rgba(99,102,241,0.4)' }}>
              <Zap className="h-4 w-4 text-white" />
            </div>
            <div>
              <div className="font-bold text-base leading-tight tracking-tight">
                <span className="text-white">Risk</span>
                <span style={{ color: '#818cf8' }}>Pulse</span>
              </div>
              <div className="text-xs mt-0.5 tracking-widest uppercase" style={{ color: '#475569', fontSize: '9px' }}>Intelligence</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-5 space-y-1">
          <p className="text-xs font-semibold uppercase tracking-widest px-3 mb-3" style={{ color: '#334155', letterSpacing: '0.12em' }}>
            Dashboards
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                  isActive
                    ? 'text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                style={isActive ? {
                  background: 'linear-gradient(135deg, #4f46e5, #6366f1)',
                  boxShadow: '0 4px 14px rgba(79,70,229,0.35)'
                } : {}}
                onMouseEnter={e => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.05)';
                }}
                onMouseLeave={e => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = '';
                }}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${
                  isActive ? 'bg-white/20' : 'bg-white/5 group-hover:bg-white/10'
                }`}>
                  <Icon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.label}</p>
                  <p className={`text-xs truncate ${isActive ? 'text-indigo-200' : 'text-slate-600'}`}>
                    {item.description}
                  </p>
                </div>
                {isActive && <ChevronRight className="h-3.5 w-3.5 text-indigo-200 flex-shrink-0" />}
              </Link>
            );
          })}
        </nav>

        {/* Status Footer */}
        <div className="px-4 pb-5">
          <div className="rounded-xl px-3.5 py-3 mb-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-center space-x-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-xs" style={{ color: '#94a3b8' }}>
                API <span className="font-semibold" style={{ color: '#34d399' }}>Connected</span>
              </span>
            </div>
            <p className="text-xs mt-1 font-mono" style={{ color: '#334155' }}>localhost:8000</p>
          </div>
          <button
            onClick={onLogout}
            className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all duration-200 text-slate-400 hover:text-slate-200"
            style={{ background: 'rgba(255,255,255,0.05)' }}
          >
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-white/5">
              <LogOut className="h-4 w-4" />
            </div>
            <span className="text-sm font-medium">Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  );
}
