import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ChatCounselor from './components/ChatCounselor';
import PetCard from './components/PetCard';
import PetDetailModal from './components/PetDetailModal';
import CompatibilityModal from './components/CompatibilityModal';
import AdoptionModal from './components/AdoptionModal';
import AuthModal from './components/AuthModal';
import { SAMPLE_PETS } from './data/samplePets';
import { listPets, getSavedPets, toggleFavorite } from './services/api';
import { Search, Heart, Sparkles, Shield, AlertCircle, RefreshCw, PawPrint, LogIn, Lock } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('explore'); // 'explore' | 'chat' | 'saved' | 'profile'
  
  // Authentication state
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('pawfect_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authTriggerReason, setAuthTriggerReason] = useState(null);

  // Pet catalog state (initialized with SAMPLE_PETS so pets are never missing!)
  const [pets, setPets] = useState(SAMPLE_PETS);
  const [savedPetIds, setSavedPetIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [isLiveBackend, setIsLiveBackend] = useState(false);

  // Filters state
  const [speciesFilter, setSpeciesFilter] = useState('all'); // 'all' | 'dog' | 'cat'
  const [kidsOnly, setKidsOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals state
  const [detailPet, setDetailPet] = useState(null);
  const [compatPet, setCompatPet] = useState(null);
  const [adoptPet, setAdoptPet] = useState(null);

  // Load live pets from backend on mount or when user changes
  useEffect(() => {
    loadLivePets();
    if (user) {
      loadSavedPets(user.user_id || user.id);
    }
  }, [user]);

  const loadLivePets = async () => {
    setLoading(true);
    try {
      const fetched = await listPets();
      if (Array.isArray(fetched) && fetched.length > 0) {
        setPets(fetched);
        setIsLiveBackend(true);
      } else {
        // Fallback to sample pets if empty
        setPets(SAMPLE_PETS);
      }
    } catch (err) {
      console.warn('Backend API not responding; using bundled sample pets catalog.', err);
      setPets(SAMPLE_PETS);
      setIsLiveBackend(false);
    } finally {
      setLoading(false);
    }
  };

  const loadSavedPets = async (userId) => {
    try {
      const saved = await getSavedPets(userId);
      const ids = new Set((saved || []).map(p => p._id || p.id));
      setSavedPetIds(ids);
    } catch (e) {
      console.warn('Could not load saved pets:', e);
    }
  };

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem('pawfect_user', JSON.stringify(userData));
    setIsAuthOpen(false);
    setAuthTriggerReason(null);
    loadSavedPets(userData.user_id || userData.id);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('pawfect_user');
    setSavedPetIds(new Set());
    setActiveTab('explore');
  };

  // Guard for protected specialties
  const requireAuth = (featureName, callback) => {
    if (!user) {
      setAuthTriggerReason(featureName);
      setIsAuthOpen(true);
      return false;
    }
    if (callback) callback();
    return true;
  };

  const handleToggleFavorite = async (petId) => {
    if (!requireAuth('Saving Favorite Pets')) return;

    const userId = user.user_id || user.id || 'user_default';
    setSavedPetIds(prev => {
      const next = new Set(prev);
      if (next.has(petId)) {
        next.delete(petId);
      } else {
        next.add(petId);
      }
      return next;
    });

    try {
      await toggleFavorite(userId, petId);
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };

  const handleTabChange = (tabId) => {
    if (tabId === 'chat' && !user) {
      requireAuth('AI Matchmaker Counselor', () => setActiveTab('chat'));
      return;
    }
    if (tabId === 'saved' && !user) {
      requireAuth('Saved Pets', () => setActiveTab('saved'));
      return;
    }
    setActiveTab(tabId);
  };

  // Filtered pets list
  const filteredPets = pets.filter(pet => {
    if (speciesFilter !== 'all' && pet.species?.toLowerCase() !== speciesFilter.toLowerCase()) return false;
    if (kidsOnly && !pet.good_with_kids) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = pet.name?.toLowerCase().includes(q);
      const matchBreed = pet.breed?.toLowerCase().includes(q);
      const matchBio = pet.bio_text?.toLowerCase().includes(q);
      const matchTemperament = pet.temperament?.some(t => t.toLowerCase().includes(q));
      if (!matchName && !matchBreed && !matchBio && !matchTemperament) return false;
    }
    return true;
  });

  const savedPetsList = pets.filter(p => savedPetIds.has(p._id || p.id));

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-stone-800 flex flex-col font-sans">
      {/* Top Header Navbar */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={handleTabChange} 
        savedCount={savedPetIds.size} 
        user={user}
        onOpenAuth={() => { setAuthTriggerReason(null); setIsAuthOpen(true); }}
        onLogout={handleLogout}
      />

      {/* Guest Banner if not signed in */}
      {!user && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs text-amber-900 flex items-center justify-between">
          <div className="max-w-6xl mx-auto w-full flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>
                <strong>Browsing as Guest.</strong> Sign in to chat with the AI counselor, evaluate compatibility, and save favorites.
              </span>
            </div>
            <button
              onClick={() => { setAuthTriggerReason('Sign In'); setIsAuthOpen(true); }}
              className="ml-3 font-bold underline hover:text-amber-800 whitespace-nowrap"
            >
              Sign In / Sign Up →
            </button>
          </div>
        </div>
      )}

      {/* Main Content Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
        
        {/* TAB 1: EXPLORE PETS CATALOG (Default Landing) */}
        {activeTab === 'explore' && (
          <div className="animate-fade-in space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-stone-900">
                  Available Shelter Pets
                </h1>
                <p className="text-sm text-stone-500 mt-1">
                  Discover loving companions ready for adoption. {isLiveBackend ? '• Live MongoDB Atlas catalog' : '• Sample catalog'}
                </p>
              </div>

              {/* AI Counselor Banner CTA */}
              <button
                onClick={() => handleTabChange('chat')}
                className="self-start sm:self-auto flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold shadow-sm transition-all"
              >
                <Sparkles className="w-4 h-4 text-amber-200" />
                Ask AI Pet Counselor
              </button>
            </div>

            {/* Filter Bar */}
            <div className="bg-white p-3.5 sm:p-4 rounded-2xl border border-stone-200/80 shadow-xs space-y-3 sm:space-y-0 sm:flex sm:items-center sm:gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by breed, name (e.g. Buddy, Luna), or temperament..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-stone-50 rounded-xl text-xs sm:text-sm border-0 focus:ring-2 focus:ring-amber-500/20 text-stone-800 placeholder-stone-400"
                />
              </div>

              {/* Species Filter */}
              <div className="flex items-center gap-1 bg-stone-50 p-1 rounded-xl">
                {['all', 'dog', 'cat'].map((spec) => (
                  <button
                    key={spec}
                    onClick={() => setSpeciesFilter(spec)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                      speciesFilter === spec
                        ? 'bg-white text-stone-900 shadow-xs'
                        : 'text-stone-500 hover:text-stone-900'
                    }`}
                  >
                    {spec === 'all' ? 'All Pets' : spec === 'dog' ? '🐶 Dogs' : '🐱 Cats'}
                  </button>
                ))}
              </div>

              {/* Kids Filter */}
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-stone-600 bg-stone-50 px-3 py-2 rounded-xl">
                <input
                  type="checkbox"
                  checked={kidsOnly}
                  onChange={(e) => setKidsOnly(e.target.checked)}
                  className="rounded text-amber-500 focus:ring-amber-500 border-stone-300"
                />
                <span>Good with kids</span>
              </label>
            </div>

            {/* Pets Grid */}
            {filteredPets.length === 0 ? (
              <div className="py-16 text-center bg-white rounded-2xl border border-stone-200/60 p-8">
                <PawPrint className="w-10 h-10 text-stone-300 mx-auto mb-3" />
                <h3 className="font-medium text-stone-700">No pets match your criteria</h3>
                <p className="text-xs text-stone-400 mt-1">Try resetting filters or expanding your search</p>
                <button
                  onClick={() => { setSpeciesFilter('all'); setKidsOnly(false); setSearchQuery(''); }}
                  className="mt-4 px-4 py-2 bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-medium rounded-xl transition-colors"
                >
                  Reset filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredPets.map((pet) => (
                  <PetCard
                    key={pet._id || pet.id}
                    pet={pet}
                    isFavorite={savedPetIds.has(pet._id || pet.id)}
                    onToggleFavorite={handleToggleFavorite}
                    onViewDetails={() => setDetailPet(pet)}
                    onCheckCompatibility={() => {
                      if (requireAuth('Compatibility Diagnostic', () => setCompatPet(pet))) {
                        setCompatPet(pet);
                      }
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: AI MATCHMAKER CHAT */}
        {activeTab === 'chat' && (
          <div className="animate-fade-in">
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-stone-900 flex items-center gap-2">
                  <span>AI Pet Adoption Counselor</span>
                  <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">LangGraph Live</span>
                </h1>
                <p className="text-sm text-stone-500 mt-1">
                  Chat conversationally about your living space, family, and schedule to receive AI recommendations.
                </p>
              </div>
            </div>
            
            <ChatCounselor 
              onViewPet={(pet) => setDetailPet(pet)}
              onAdoptPet={(pet) => {
                if (requireAuth('Adoption Application', () => setAdoptPet(pet))) {
                  setAdoptPet(pet);
                }
              }}
            />
          </div>
        )}

        {/* TAB 3: SAVED PETS */}
        {activeTab === 'saved' && (
          <div className="animate-fade-in space-y-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-stone-900">
                Your Saved Pets
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Your shortlisted companion animals for adoption consideration.
              </p>
            </div>

            {savedPetsList.length === 0 ? (
              <div className="py-20 text-center bg-white rounded-2xl border border-dashed border-stone-200 p-8">
                <Heart className="w-12 h-12 text-stone-300 mx-auto mb-3" />
                <h3 className="font-semibold text-stone-800 text-base">No saved pets yet</h3>
                <p className="text-xs text-stone-400 mt-1 max-w-sm mx-auto">
                  Click the heart icon on any pet card in Explore to save them here for side-by-side comparison.
                </p>
                <button
                  onClick={() => setActiveTab('explore')}
                  className="mt-5 px-5 py-2.5 bg-stone-900 text-white text-xs font-semibold rounded-xl hover:bg-stone-800 transition-colors shadow-sm"
                >
                  Browse Available Pets
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {savedPetsList.map((pet) => (
                  <PetCard
                    key={pet._id || pet.id}
                    pet={pet}
                    isFavorite={true}
                    onToggleFavorite={handleToggleFavorite}
                    onViewDetails={() => setDetailPet(pet)}
                    onCheckCompatibility={() => setCompatPet(pet)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: PROFILE & APPLICATIONS */}
        {activeTab === 'profile' && (
          <div className="animate-fade-in space-y-6 max-w-3xl">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-stone-900">
                Adopter Profile Hub
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Manage your lifestyle preferences used by the AI matcher.
              </p>
            </div>

            {user ? (
              <div className="space-y-6">
                {/* Profile Card */}
                <div className="bg-white rounded-2xl border border-stone-200/80 p-6 shadow-xs space-y-6">
                  <div className="flex items-center justify-between pb-6 border-b border-stone-100">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-700 flex items-center justify-center text-xl font-bold border border-amber-500/20">
                        {(user.name || user.email || 'U')[0].toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-bold text-stone-900 text-lg">{user.name || 'Adopter'}</h3>
                        <p className="text-xs text-stone-500">{user.email} • ID: {user.user_id || user.id}</p>
                      </div>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="px-3 py-1.5 text-xs text-stone-600 hover:text-stone-900 hover:bg-stone-100 rounded-lg transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
                    <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                      <span className="text-[10px] text-stone-400 block font-semibold uppercase tracking-wider">Housing</span>
                      <span className="text-xs font-semibold text-stone-800 mt-1 block capitalize">
                        {(user.housing_type || 'apartment').replace('_', ' ')}
                      </span>
                    </div>
                    <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                      <span className="text-[10px] text-stone-400 block font-semibold uppercase tracking-wider">Children</span>
                      <span className="text-xs font-semibold text-stone-800 mt-1 block">
                        {user.has_children ? 'Yes (Kids at home)' : 'No children'}
                      </span>
                    </div>
                    <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                      <span className="text-[10px] text-stone-400 block font-semibold uppercase tracking-wider">Resident Pets</span>
                      <span className="text-xs font-semibold text-stone-800 mt-1 block">
                        {user.has_other_pets ? 'Yes (Other pets)' : 'None'}
                      </span>
                    </div>
                    <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                      <span className="text-[10px] text-stone-400 block font-semibold uppercase tracking-wider">Energy Budget</span>
                      <span className="text-xs font-semibold text-stone-800 mt-1 block">
                        {user.energy_budget || 3}/5 Active
                      </span>
                    </div>
                    <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                      <span className="text-[10px] text-stone-400 block font-semibold uppercase tracking-wider">Saved Pets</span>
                      <span className="text-xs font-semibold text-amber-700 mt-1 block">
                        {savedPetIds.size} Pets
                      </span>
                    </div>
                    <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                      <span className="text-[10px] text-stone-400 block font-semibold uppercase tracking-wider">Status</span>
                      <span className="text-xs font-semibold text-emerald-700 mt-1 block">
                        Ready to Adopt
                      </span>
                    </div>
                  </div>
                </div>

                {/* Telemetry card */}
                <div className="bg-stone-900 text-stone-300 rounded-2xl p-6 shadow-xs text-xs space-y-3">
                  <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
                    <Shield className="w-4 h-4" />
                    PawFect System Status
                  </div>
                  <p className="leading-relaxed text-stone-400">
                    Connected to FastAPI backend with MongoDB Atlas Vector Search index (<code className="text-amber-300">vector_index</code>) 
                    and LangGraph Multi-Turn State Graph persistence.
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    <span className="bg-stone-800 text-stone-300 px-2.5 py-1 rounded-lg">REST: /api/v1 Active</span>
                    <span className="bg-stone-800 text-stone-300 px-2.5 py-1 rounded-lg">Catalog: {pets.length} Available</span>
                    <span className="bg-stone-800 text-stone-300 px-2.5 py-1 rounded-lg">SSE Streaming: Enabled</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-stone-200/80 p-8 text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-600 flex items-center justify-center mx-auto text-xl">
                  <Lock className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-stone-800 text-lg">Sign in to view your profile</h3>
                <p className="text-xs text-stone-500 max-w-sm mx-auto">
                  Create an account or sign in to customize your home environment parameters and track your adoption applications.
                </p>
                <button
                  onClick={() => setIsAuthOpen(true)}
                  className="px-6 py-2.5 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold rounded-xl transition-all shadow-sm inline-flex items-center gap-2"
                >
                  <LogIn className="w-4 h-4" />
                  Sign In or Create Account
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="border-t border-stone-200/60 py-6 text-center text-xs text-stone-400">
        <p>PawFect © 2026 — AI Pet Matchmaker. Built with Jetpack Compose & React.</p>
      </footer>

      {/* AUTHENTICATION / LOGIN / SIGN UP MODAL */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => { setIsAuthOpen(false); setAuthTriggerReason(null); }}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* MODAL 1: PET DETAIL MODAL */}
      <PetDetailModal
        pet={detailPet}
        isOpen={Boolean(detailPet)}
        onClose={() => setDetailPet(null)}
        isFavorite={detailPet ? savedPetIds.has(detailPet._id || detailPet.id) : false}
        onToggleFavorite={handleToggleFavorite}
        onCheckCompatibility={(pet) => {
          setDetailPet(null);
          if (requireAuth('Compatibility Diagnostic', () => setCompatPet(pet))) {
            setCompatPet(pet);
          }
        }}
        onStartAdoption={(pet) => {
          setDetailPet(null);
          if (requireAuth('Adoption Application', () => setAdoptPet(pet))) {
            setAdoptPet(pet);
          }
        }}
      />

      {/* MODAL 2: COMPATIBILITY EVALUATION MODAL */}
      <CompatibilityModal
        pet={compatPet}
        isOpen={Boolean(compatPet)}
        onClose={() => setCompatPet(null)}
        onContinueAdoption={(pet) => {
          setCompatPet(null);
          if (requireAuth('Adoption Application', () => setAdoptPet(pet))) {
            setAdoptPet(pet);
          }
        }}
      />

      {/* MODAL 3: 4-STAGE ADOPTION APPLICATION MODAL */}
      <AdoptionModal
        pet={adoptPet}
        isOpen={Boolean(adoptPet)}
        onClose={() => setAdoptPet(null)}
      />
    </div>
  );
}
