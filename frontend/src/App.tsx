import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { DashboardPage } from './pages/DashboardPage';
import { HidePage } from './pages/HidePage';
import { ExtractPage } from './pages/ExtractPage';
import { VerifyPage } from './pages/VerifyPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';
import { HealthInfo } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const info = await api.getHealth();
        setHealth(info);
      } catch (err) {
        console.warn('Backend connection error:', err);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage onNavigate={setActiveTab} health={health} />;
      case 'hide':
        return <HidePage />;
      case 'extract':
        return <ExtractPage />;
      case 'verify':
        return <VerifyPage />;
      case 'settings':
        return <SettingsPage health={health} />;
      default:
        return <DashboardPage onNavigate={setActiveTab} health={health} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#05020c] text-purple-100 flex flex-col selection:bg-fuchsia-600 selection:text-white relative overflow-x-hidden">
      {/* Background Ambient Radial Glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-6xl h-[650px] bg-purple-radial opacity-90 blur-2xl" />
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[480px] h-[220px] bg-fuchsia-500/20 rounded-full blur-[80px]" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-[400px] bg-purple-bottom-radial opacity-60 blur-3xl" />
      </div>

      {/* Redesigned Cyber Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
        {renderContent()}
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default App;
