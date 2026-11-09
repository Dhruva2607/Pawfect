import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ChatCounselor from './components/ChatCounselor';
import PetCard from './components/PetCard';
import PetDetailModal from './components/PetDetailModal';
import CompatibilityModal from './components/CompatibilityModal';
import AdoptionModal from './components/AdoptionModal';
import { listPets, getSavedPets, toggleFavorite, getAdoptionStatus } from './services/api';
import { Search, SlidersHorizontal, Heart, Sparkles, Home, Shield, AlertCircle, RefreshCw, PawPrint, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'explore' | 'saved' | 'profile'
  
  // Pet catalog state
  const [pets, setPets] = useState([]);
  const [savedPetIds, setSavedPetIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [speciesFilter, setSpeciesFilter] = useState('all'); // 'all' | 'dog' | 'cat'
  const [sizeFilter, setSizeFilter] = useState('all'); // 'all' | 'small' | 'medium' | 'large'
  const [kidsOnly, setKidsOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals state
  const [detailPet, setDetailPet] = useState(null);
  const [compatPet, setCompatPet] = useState(null);
  const [adoptPet, setAdoptPet] = useState(null);

  // Profile / Adoption applications state
  const [trackedApplications, setTrackedApplications] = useState(() => {
    try {
      const saved = localStorage.getItem('pawfect_applications');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Load pets and saved favorites on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [petsData, savedData] = await Promise.allSettled([
        listPets(),
        getSavedPets('user_default')
      ]);

      if (petsData.status === 'fulfilled') {
        setPets(petsData.value.pets || []);
      } else {
        throw new Error('Failed to load pets from backend');
      }

      if (savedData.status === 'fulfilled') {
        const ids = new Set((savedData.value.saved_pets || []).map(p => p._id || p.id));
        setSavedPetIds(ids);
      }
    } catch (err) {
      console.error(err);
      setError('Could not connect to PawFect backend at http://localhost:8000. Ensure the FastAPI server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async (petId) => {
    // Optimistic toggle
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
      await toggleFavorite('user_default', petId);
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };

  const handleOpenAdoption = (pet) => {
    setAdoptPet(pet);
  };

  const handleOpenCompatibility = (pet) => {
    setCompatPet(pet);
  };

  // Filtered pets list
  const filteredPets = pets.filter(pet => {
    if (speciesFilter !== 'all' && pet.species !== speciesFilter) return false;
    if (sizeFilter !== 'all' && pet.size !== sizeFilter) return false;
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

  // Saved pets list
  const savedPetsList = pets.filter(p => savedPetIds.has(p._id || p.id));

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-stone-800 flex flex-col font-sans">
      {/* Minimal Top Header */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        savedCount={savedPetIds.size} 
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
        
        {/* Error notification if backend unavailable */}
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button 
              onClick={loadData}
              className="px-3 py-1.5 bg-amber-200/70 hover:bg-amber-200 rounded-xl font-medium text-xs transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry
            </button>
          </div>
        )}

        {/* TAB 1: AI MATCHMAKER CHAT */}
        {activeTab === 'chat' && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-stone-900">
                AI Pet Counselor
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Conversational matchmaking powered by LangGraph, MongoDB Vector Search, and Gemini 2026.
              </p>
            </div>
            
            <ChatCounselor 
              onViewPet={(pet) => setDetailPet(pet)}
              onAdoptPet={(pet) => setAdoptPet(pet)}
            />
          </div>
        )}

        {/* TAB 2: EXPLORE PETS CATALOG */}
        {activeTab === 'explore' && (
          <div className="animate-fade-in space-y-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-stone-900">
                Meet Available Pets
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Browse our verified shelter pets waiting for their forever home.
              </p>
            </div>

            {/* Filter Bar */}
            <div className="bg-white p-4 rounded-2xl border border-stone-200/70 shadow-sm space-y-3 sm:space-y-0 sm:flex sm:items-center sm:gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by name, breed, or temperament..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-stone-50 rounded-xl text-sm border-0 focus:ring-2 focus:ring-amber-500/20 text-stone-800 placeholder-stone-400"
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
                        ? 'bg-white text-stone-900 shadow-sm'
                        : 'text-stone-500 hover:text-stone-900'
                    }`}
                  >
                    {spec === 'all' ? 'All Species' : spec === 'dog' ? '🐶 Dogs' : '🐱 Cats'}
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

            {/* Grid */}
            {loading ? (
              <div className="py-20 text-center text-stone-400 text-sm">
                <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                Loading pet catalog...
              </div>
            ) : filteredPets.length === 0 ? (
              <div className="py-16 text-center bg-white rounded-2xl border border-stone-200/60 p-8">
                <PawPrint className="w-10 h-10 text-stone-300 mx-auto mb-3" />
                <h3 className="font-medium text-stone-700">No pets match your criteria</h3>
                <p className="text-xs text-stone-400 mt-1">Try resetting filters or expanding your search</p>
                <button
                  onClick={() => { setSpeciesFilter('all'); setSizeFilter('all'); setKidsOnly(false); setSearchQuery(''); }}
                  className="mt-4 px-4 py-2 bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-medium rounded-xl transition-colors"
                >
                  Reset all filters
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
                    onCheckCompatibility={() => handleOpenCompatibility(pet)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SAVED PETS */}
        {activeTab === 'saved' && (
          <div className="animate-fade-in space-y-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-stone-900">
                Your Saved Pets
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Keep track of your favorite furry friends as you decide on adoption.
              </p>
            </div>

            {savedPetsList.length === 0 ? (
              <div className="py-20 text-center bg-white rounded-2xl border border-dashed border-stone-200 p-8">
                <Heart className="w-12 h-12 text-stone-300 mx-auto mb-3" />
                <h3 className="font-medium text-stone-800 text-base">No saved pets yet</h3>
                <p className="text-xs text-stone-400 mt-1 max-w-sm mx-auto">
                  Click the heart icon on any pet card in Explore or Chat to save them here for quick comparison.
                </p>
                <button
                  onClick={() => setActiveTab('explore')}
                  className="mt-5 px-5 py-2.5 bg-stone-900 text-white text-xs font-medium rounded-xl hover:bg-stone-800 transition-colors shadow-sm"
                >
                  Explore Pets
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
                    onCheckCompatibility={() => handleOpenCompatibility(pet)}
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
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-stone-900">
                Adopter Profile
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Your lifestyle profile used by the AI counselor to calculate compatibility.
              </p>
            </div>

            {/* Profile Summary Card */}
            <div className="bg-white rounded-2xl border border-stone-200/70 p-6 shadow-sm space-y-6">
              <div className="flex items-center gap-4 pb-6 border-b border-stone-100">
                <div className="w-14 h-14 rounded-2xl bg-amber-100/70 text-amber-700 flex items-center justify-center text-xl font-bold">
                  JD
                </div>
                <div>
                  <h3 className="font-semibold text-stone-900 text-lg">Jane Doe</h3>
                  <p className="text-xs text-stone-500">ID: user_default • Active Searcher</p>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                  <span className="text-[11px] text-stone-400 block font-medium uppercase tracking-wider">Housing</span>
                  <span className="text-sm font-semibold text-stone-800 mt-0.5 block">Apartment (Balcony)</span>
                </div>
                <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                  <span className="text-[11px] text-stone-400 block font-medium uppercase tracking-wider">Fenced Yard</span>
                  <span className="text-sm font-semibold text-stone-800 mt-0.5 block">No Yard</span>
                </div>
                <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                  <span className="text-[11px] text-stone-400 block font-medium uppercase tracking-wider">Activity Level</span>
                  <span className="text-sm font-semibold text-stone-800 mt-0.5 block">Moderate (3/5)</span>
                </div>
                <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                  <span className="text-[11px] text-stone-400 block font-medium uppercase tracking-wider">Children</span>
                  <span className="text-sm font-semibold text-stone-800 mt-0.5 block">1 Child (6 yrs)</span>
                </div>
                <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                  <span className="text-[11px] text-stone-400 block font-medium uppercase tracking-wider">Resident Pets</span>
                  <span className="text-sm font-semibold text-stone-800 mt-0.5 block">None</span>
                </div>
                <div className="bg-stone-50 p-3.5 rounded-xl border border-stone-100">
                  <span className="text-[11px] text-stone-400 block font-medium uppercase tracking-wider">Experience</span>
                  <span className="text-sm font-semibold text-stone-800 mt-0.5 block">First-time Owner</span>
                </div>
              </div>
            </div>

            {/* Architecture Details Card */}
            <div className="bg-stone-900 text-stone-300 rounded-2xl p-6 shadow-sm text-xs space-y-3">
              <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
                <Shield className="w-4 h-4" />
                PawFect System Telemetry
              </div>
              <p className="leading-relaxed text-stone-400">
                Connected to FastAPI backend with MongoDB Atlas Vector Search index (<code className="text-amber-300">vector_index</code>) 
                and LangGraph Multi-Turn State Graph persistence via MongoDBSaver checkpointer.
              </p>
              <div className="flex flex-wrap gap-2 pt-2">
                <span className="bg-stone-800 text-stone-300 px-2.5 py-1 rounded-lg">REST: 10 Endpoints Active</span>
                <span className="bg-stone-800 text-stone-300 px-2.5 py-1 rounded-lg">SSE: Streaming SSE /chat/message</span>
                <span className="bg-stone-800 text-stone-300 px-2.5 py-1 rounded-lg">Embeddings: 768-dim</span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="border-t border-stone-200/60 py-6 text-center text-xs text-stone-400">
        <p>PawFect © 2026 — AI-Powered Pet Matchmaker. Built with Jetpack Compose & React.</p>
      </footer>

      {/* MODAL 1: PET DETAIL MODAL */}
      <PetDetailModal
        pet={detailPet}
        isOpen={Boolean(detailPet)}
        onClose={() => setDetailPet(null)}
        isFavorite={detailPet ? savedPetIds.has(detailPet._id || detailPet.id) : false}
        onToggleFavorite={handleToggleFavorite}
        onCheckCompatibility={(pet) => {
          setDetailPet(null);
          setCompatPet(pet);
        }}
        onStartAdoption={(pet) => {
          setDetailPet(null);
          setAdoptPet(pet);
        }}
      />

      {/* MODAL 2: COMPATIBILITY EVALUATION MODAL */}
      <CompatibilityModal
        pet={compatPet}
        isOpen={Boolean(compatPet)}
        onClose={() => setCompatPet(null)}
        onContinueAdoption={(pet) => {
          setCompatPet(null);
          setAdoptPet(pet);
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
