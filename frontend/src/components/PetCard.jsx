import React from 'react';
import { Heart, Sparkles, MapPin, Check } from 'lucide-react';
import CircularGauge from './CircularGauge';

export default function PetCard({
  pet,
  isFavorite = false,
  onToggleFavorite,
  onViewDetails,
  onCheckCompatibility,
  score = null
}) {
  return (
    <div className="group bg-white rounded-2xl border border-stone-200/70 overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 flex flex-col">
      {/* Photo Header */}
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-stone-100">
        <img
          src={pet.photo_url || 'https://images.unsplash.com/photo-1552053831-71594a27632d'}
          alt={pet.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/10" />

        {/* Favorite Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleFavorite(pet._id);
          }}
          className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center text-stone-600 hover:text-rose-500 transition-colors shadow-sm"
        >
          <Heart className={`w-4 h-4 ${isFavorite ? 'fill-rose-500 text-rose-500' : ''}`} />
        </button>

        {/* Score Gauge Badge if provided */}
        {score !== null && (
          <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md rounded-2xl p-1 shadow-md">
            <CircularGauge score={score} size={54} strokeWidth={5} />
          </div>
        )}

        {/* Species & Gender Badge */}
        <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md text-white text-xs font-medium px-2.5 py-1 rounded-full">
          {pet.gender} • {pet.species === 'dog' ? '🐶' : '🐱'}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold text-lg text-stone-900 leading-snug group-hover:text-amber-600 transition-colors">
                {pet.name}
              </h3>
              <p className="text-sm text-stone-500">{pet.breed} • {Math.floor(pet.age_months / 12) || pet.age_months} {pet.age_months >= 24 ? 'yrs' : 'mos'}</p>
            </div>
            <div className="flex items-center gap-0.5 text-xs text-stone-400 bg-stone-50 border border-stone-100 rounded-lg px-2 py-1">
              <span>Energy:</span>
              <span className="font-semibold text-stone-700 ml-1">{pet.energy_level}/5</span>
            </div>
          </div>

          {/* Temperament chips */}
          <div className="flex flex-wrap gap-1.5 mt-3">
            {pet.temperament?.slice(0, 3).map((tag, idx) => (
              <span
                key={idx}
                className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-stone-100 text-stone-600 border border-stone-200/50"
              >
                {tag}
              </span>
            ))}
          </div>

          <p className="text-xs text-stone-600 mt-3 line-clamp-2 leading-relaxed">
            {pet.bio_text}
          </p>
        </div>

        {/* Actions */}
        <div className="mt-5 pt-3 border-t border-stone-100 flex items-center gap-2">
          <button
            onClick={() => onViewDetails(pet)}
            className="flex-1 py-2 px-3 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200/70 rounded-xl transition-colors"
          >
            Profile
          </button>
          <button
            onClick={() => onCheckCompatibility(pet)}
            className="flex-1 py-2 px-3 text-xs font-medium text-amber-900 bg-amber-100/80 hover:bg-amber-200/80 rounded-xl transition-colors flex items-center justify-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            Check Match
          </button>
        </div>
      </div>
    </div>
  );
}
