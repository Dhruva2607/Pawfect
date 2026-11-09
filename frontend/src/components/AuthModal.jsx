import React, { useState } from 'react';
import { X, Lock, Mail, User, Sparkles, Home, Heart, ArrowRight, ShieldCheck, Check } from 'lucide-react';
import { loginUser, signupUser } from '../services/api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = 'signin' }) {
  if (!isOpen) return null;

  const [mode, setMode] = useState(initialMode); // 'signin' | 'signup'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // Lifestyle questionnaire during sign up
  const [housingType, setHousingType] = useState('apartment');
  const [hasChildren, setHasChildren] = useState(true);
  const [hasOtherPets, setHasOtherPets] = useState(false);
  const [energyBudget, setEnergyBudget] = useState(3);

  const handleDemoSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const demoUser = await loginUser({
        email: 'jane.doe@pawfect.app',
        password: 'password123'
      });
      onAuthSuccess({
        ...demoUser,
        name: 'Jane Doe',
        housing_type: 'apartment',
        has_children: true,
        has_other_pets: false,
        energy_budget: 3
      });
      onClose();
    } catch (err) {
      console.error(err);
      setError('Failed to sign in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      setError('Please provide a valid email address.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      let userData;
      if (mode === 'signin') {
        userData = await loginUser({ email, password });
      } else {
        userData = await signupUser({
          name: name || email.split('@')[0],
          email,
          password,
          housing_type: housingType,
          has_children: hasChildren,
          has_other_pets: hasOtherPets,
          energy_budget: energyBudget
        });
      }

      onAuthSuccess(userData);
      onClose();
    } catch (err) {
      console.error(err);
      setError('Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/50 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-stone-200/80 overflow-hidden relative flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-9 h-9 rounded-full bg-stone-100 hover:bg-stone-200 text-stone-500 hover:text-stone-800 flex items-center justify-center transition-colors z-10"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header Hero */}
        <div className="p-6 pb-4 bg-gradient-to-b from-amber-500/10 via-amber-500/5 to-transparent text-center">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-2xl flex items-center justify-center mx-auto mb-3 shadow-inner">
            🐾
          </div>
          <h2 className="text-xl font-bold tracking-tight text-stone-900">
            {mode === 'signin' ? 'Welcome Back to PawFect' : 'Unlock Your AI Pet Match'}
          </h2>
          <p className="text-xs text-stone-500 mt-1 max-w-xs mx-auto">
            {mode === 'signin'
              ? 'Sign in to access AI counseling, compatibility diagnostics, and adoption applications.'
              : 'Create your adopter profile to get custom-matched with shelter pets.'}
          </p>

          {/* Mode Switcher Tabs */}
          <div className="mt-5 flex p-1 bg-stone-100 rounded-xl">
            <button
              type="button"
              onClick={() => { setMode('signin'); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'signin'
                  ? 'bg-white text-stone-900 shadow-sm'
                  : 'text-stone-500 hover:text-stone-900'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode('signup'); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'signup'
                  ? 'bg-white text-stone-900 shadow-sm'
                  : 'text-stone-500 hover:text-stone-900'
              }`}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Quick Demo Sign In Button */}
        <div className="px-6 pt-2">
          <button
            type="button"
            onClick={handleDemoSignIn}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-amber-50 hover:bg-amber-100/80 border border-amber-200/70 text-amber-900 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-2 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            Quick Demo Sign In (Jane Doe)
          </button>
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-stone-200" /></div>
            <div className="relative flex justify-center text-[10px] uppercase font-semibold text-stone-400 bg-white px-2">
              <span>Or with email</span>
            </div>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-3.5 max-h-[60vh] overflow-y-auto">
          {error && (
            <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {error}
            </div>
          )}

          {/* Name Field (Sign up only) */}
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-stone-700 mb-1">Your Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Alex Morgan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-xs text-stone-900 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
            </div>
          )}

          {/* Email Field */}
          <div>
            <label className="block text-xs font-medium text-stone-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-xs text-stone-900 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label className="block text-xs font-medium text-stone-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-xs text-stone-900 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>
          </div>

          {/* Lifestyle survey fields for Sign Up */}
          {mode === 'signup' && (
            <div className="pt-2 border-t border-stone-100 space-y-3">
              <p className="text-[11px] font-semibold text-stone-700 uppercase tracking-wider">
                Lifestyle Baseline (for AI matching)
              </p>

              <div>
                <label className="block text-[11px] font-medium text-stone-600 mb-1">Housing Type</label>
                <select
                  value={housingType}
                  onChange={(e) => setHousingType(e.target.value)}
                  className="w-full py-1.5 px-3 bg-stone-50 border border-stone-200 rounded-xl text-xs text-stone-800"
                >
                  <option value="apartment">Apartment</option>
                  <option value="apartment_or_house">Apartment with Balcony / Patio</option>
                  <option value="house_with_yard">House with Fenced Yard</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <label className="flex items-center gap-2 p-2 bg-stone-50 rounded-xl border border-stone-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasChildren}
                    onChange={(e) => setHasChildren(e.target.checked)}
                    className="rounded text-amber-500 focus:ring-amber-500 border-stone-300"
                  />
                  <span className="text-stone-700 text-[11px]">Kids in home</span>
                </label>

                <label className="flex items-center gap-2 p-2 bg-stone-50 rounded-xl border border-stone-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasOtherPets}
                    onChange={(e) => setHasOtherPets(e.target.checked)}
                    className="rounded text-amber-500 focus:ring-amber-500 border-stone-300"
                  />
                  <span className="text-stone-700 text-[11px]">Other pets</span>
                </label>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-stone-600 mb-1">
                  <span>Activity / Energy Preference</span>
                  <span className="font-semibold text-amber-700">{energyBudget}/5</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={energyBudget}
                  onChange={(e) => setEnergyBudget(parseInt(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>
            </div>
          )}

          {/* Action Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 py-2.5 px-4 bg-stone-900 hover:bg-stone-800 text-white font-semibold text-xs rounded-xl transition-all shadow-md flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>{mode === 'signin' ? 'Sign In & Unlock Features' : 'Create Profile & Continue'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>

          {/* Guest fallback link */}
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={onClose}
              className="text-[11px] text-stone-500 hover:text-stone-800 underline transition-colors"
            >
              Continue browsing catalog as Guest
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

