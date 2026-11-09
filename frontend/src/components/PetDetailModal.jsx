import React from 'react';
import { X, Sparkles, Heart, Activity, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function PetDetailModal({
  pet,
  isOpen,
  onClose,
  isFavorite = false,
  onToggleFavorite,
  onCheckCompatibility,
  onStartAdoption
}) {
  if (!isOpen || !pet) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-white rounded-3xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-stone-200/80 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Photo Header */}
        <div className="relative h-64 sm:h-72 w-full bg-stone-100">
          <img
            src={pet.photo_url || 'https://images.unsplash.com/photo-1552053831-71594a27632d'}
            alt={pet.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />

          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 left-4 w-9 h-9 rounded-full bg-white/90 backdrop-blur-md flex items-center justify-center text-stone-700 hover:bg-white shadow-sm transition-all"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Favorite button */}
          <button
            onClick={() => onToggleFavorite(pet._id)}
            className="absolute top-4 right-4 w-9 h-9 rounded-full bg-white/90 backdrop-blur-md flex items-center justify-center text-stone-700 hover:text-rose-500 shadow-sm transition-all"
          >
            <Heart className={`w-5 h-5 ${isFavorite ? 'fill-rose-500 text-rose-500' : ''}`} />
          </button>

          {/* Name & Basic info in header overlay */}
          <div className="absolute bottom-4 left-5 right-5 text-white">
            <span className="text-xs uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/90 text-white inline-block mb-1">
              {pet.species === 'dog' ? 'Dog' : 'Cat'} • {pet.housing_requirement?.replace('_', ' ')}
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold leading-tight">{pet.name}</h2>
            <p className="text-sm text-stone-200">
              {pet.breed} • {pet.gender} • {pet.age_months} months old • Size: {pet.size}
            </p>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Temperament Tags */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-stone-600 mb-2">
              Temperament & Vibe
            </h4>
            <div className="flex flex-wrap gap-2">
              {pet.temperament?.map((tag, idx) => (
                <span
                  key={idx}
                  className="text-xs font-medium px-3 py-1 rounded-full bg-stone-100 text-stone-700 border border-stone-200/60"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Narrative Bio */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
              About {pet.name}
            </h4>
            <p className="text-sm text-stone-700 leading-relaxed">
              {pet.bio_text}
            </p>
          </div>

          {/* Lifestyle Grid */}
          <div className="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-stone-50 border border-stone-100">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-600 block">
                Energy Level
              </span>
              <span className="text-sm font-semibold text-stone-800">
                {pet.energy_level}/5 ({pet.energy_level >= 4 ? 'High Energy' : pet.energy_level === 3 ? 'Moderate' : 'Low / Chill'})
              </span>
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-600 block">
                Children & Family
              </span>
              <span className="text-sm font-semibold text-stone-800">
                {pet.good_with_kids ? '✓ Great with kids' : 'Best in adult home'}
              </span>
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-600 block">
                Resident Pets
              </span>
              <span className="text-sm font-semibold text-stone-800">
                {pet.good_with_other_pets ? '✓ Friendly with pets' : 'Prefers sole companion'}
              </span>
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-600 block">
                Housing
              </span>
              <span className="text-sm font-semibold text-stone-800 capitalize">
                {pet.housing_requirement?.replace(/_/g, ' ')}
              </span>
            </div>
          </div>

          {/* Exercise & Habits */}
          {pet.exercise_needs && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                Exercise Requirements
              </h4>
              <p className="text-sm text-stone-600">{pet.exercise_needs}</p>
            </div>
          )}

          {/* Quirks & Triggers */}
          {pet.quirks?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                Fun Quirks
              </h4>
              <ul className="text-xs text-stone-600 space-y-1">
                {pet.quirks.map((q, idx) => (
                  <li key={idx} className="flex items-center gap-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {pet.triggers?.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200/60">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Known Sensitivities / Triggers
              </div>
              <ul className="text-xs text-amber-900/80 space-y-0.5">
                {pet.triggers.map((t, idx) => (
                  <li key={idx}>• {t}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Modal Footer CTAs */}
        <div className="p-5 border-t border-stone-100 bg-stone-50/50 flex items-center gap-3">
          <button
            onClick={() => {
              onClose();
              onCheckCompatibility(pet);
            }}
            className="flex-1 py-3 px-4 text-sm font-medium text-stone-800 bg-white border border-stone-300/80 hover:bg-stone-100 rounded-xl transition-all shadow-2xs flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-amber-500" />
            Compatibility Score
          </button>
          <button
            onClick={() => {
              onClose();
              onStartAdoption(pet);
            }}
            className="flex-1 py-3 px-4 text-sm font-medium text-white bg-stone-900 hover:bg-stone-800 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2"
          >
            Adopt {pet.name} 🐾
          </button>
        </div>
      </div>
    </div>
  );
}
