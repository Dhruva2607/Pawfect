import React from 'react';
import { Heart, Sparkles, Compass, User, LogIn, LogOut, CheckCircle2 } from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  savedCount = 0,
  user = null,
  onOpenAuth,
  onLogout
}) {
  const tabs = [
    { id: 'explore', label: 'Explore Pets', icon: Compass },
    { id: 'chat', label: 'AI Matchmaker', icon: Sparkles, badge: 'AI' },
    { id: 'saved', label: `Saved (${savedCount})`, icon: Heart },
    { id: 'profile', label: 'Profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#FAF9F6]/90 backdrop-blur-md border-b border-stone-200/60">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-2">
        {/* Brand */}
        <div 
          onClick={() => setActiveTab('explore')}
          className="flex items-center gap-2.5 cursor-pointer group flex-shrink-0"
        >
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600 font-bold group-hover:bg-amber-500 group-hover:text-white transition-all">
            🐾
          </div>
          <div>
            <span className="font-semibold text-lg tracking-tight text-stone-900">PawFect</span>
            <span className="hidden md:inline-block ml-2 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/50">
              AI Matchmaker
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto no-scrollbar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-stone-900 text-white shadow-sm'
                    : 'text-stone-600 hover:text-stone-900 hover:bg-stone-200/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-amber-400' : 'text-stone-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Auth status / Sign In Button */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {user ? (
            <div className="flex items-center gap-2">
              <div 
                onClick={() => setActiveTab('profile')}
                className="cursor-pointer flex items-center gap-2 pl-2 pr-3 py-1 rounded-full bg-white border border-stone-200/80 hover:border-stone-300 shadow-xs transition-colors"
              >
                <div className="w-6 h-6 rounded-full bg-amber-500 text-white text-[11px] font-bold flex items-center justify-center">
                  {(user.name || user.email || 'U')[0].toUpperCase()}
                </div>
                <span className="text-xs font-semibold text-stone-800 hidden sm:inline max-w-[100px] truncate">
                  {user.name || user.email.split('@')[0]}
                </span>
              </div>
              <button
                onClick={onLogout}
                title="Sign Out"
                className="w-8 h-8 rounded-full bg-stone-100 hover:bg-stone-200 text-stone-500 hover:text-stone-800 flex items-center justify-center transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-1.5 px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl text-xs sm:text-sm font-semibold bg-amber-500 hover:bg-amber-600 text-white shadow-sm transition-all"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
