import React from 'react';
import {
  Lock,
  Unlock,
  CheckCircle2,
  Sliders,
  LayoutDashboard,
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'hide', label: 'Hide Data', icon: Lock },
    { id: 'extract', label: 'Extract Data', icon: Unlock },
    { id: 'verify', label: 'Verify Media', icon: CheckCircle2 },
    { id: 'settings', label: 'Config', icon: Sliders },
  ];

  return (
    <header className="sticky top-0 z-50 w-full bg-[#05020c]/90 backdrop-blur-xl border-b border-purple-500/20 shadow-[0_8px_30px_rgba(0,0,0,0.8)]">
      {/* Top subtle laser accent line */}
      <div className="h-[1.5px] w-full bg-gradient-to-r from-transparent via-fuchsia-500 to-transparent shadow-[0_0_10px_#d946ef]" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <div
          className="flex items-center space-x-3 cursor-pointer group select-none"
          onClick={() => setActiveTab('dashboard')}
        >
          <div className="relative w-9 h-9 sm:w-10 sm:h-10 rounded-xl overflow-hidden border border-fuchsia-500/50 shadow-[0_0_15px_rgba(217,70,239,0.5)] group-hover:shadow-[0_0_22px_rgba(217,70,239,0.8)] transition-all duration-300 bg-black shrink-0">
            <img
              src="/valicrypt-logo.jpg"
              alt="ValiCrypt"
              className="w-full h-full object-cover scale-110 group-hover:scale-120 transition-transform duration-300"
            />
          </div>

          <div className="flex flex-col">
            <div className="flex items-baseline space-x-1.5">
              <span className="font-heading font-extrabold text-xl tracking-tight text-white group-hover:text-fuchsia-200 transition-colors">
                ValiCrypt
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-fuchsia-950/80 text-fuchsia-300 border border-fuchsia-500/30 uppercase tracking-widest">
                PRO
              </span>
            </div>
            <span className="text-[10px] font-mono text-purple-400/50 hidden sm:block -mt-0.5">
              Zero-Knowledge Stego Vault
            </span>
          </div>
        </div>

        {/* Clean Cyber Navigation (No outer border, custom font style) */}
        <nav className="hidden md:flex items-center space-x-1 sm:space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg font-mono text-[11px] uppercase tracking-wider font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-800/80 via-fuchsia-800/80 to-purple-800/80 text-white shadow-[0_0_15px_rgba(217,70,239,0.4)] border border-fuchsia-400/50'
                    : 'text-purple-300/70 hover:text-white hover:bg-purple-950/40 border border-transparent'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-fuchsia-300' : 'text-purple-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Minimalist Right Status Indicator */}
        <div className="hidden sm:flex items-center space-x-2 text-[11px] font-mono text-purple-400/60">
          <span className="inline-block w-2 h-2 rounded-full bg-fuchsia-400 shadow-[0_0_8px_#d946ef] animate-pulse" />
          <span>ARMED</span>
        </div>
      </div>

      {/* Mobile Navigation Tabs (No outer border, font style matching) */}
      <div className="md:hidden border-t border-purple-500/15 px-3 py-2 flex space-x-1 overflow-x-auto scrollbar-none bg-[#0a0418]/90">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-wider font-semibold whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-purple-900/80 text-white border border-fuchsia-400/50 shadow-sm'
                  : 'text-purple-300/70 hover:text-white'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
