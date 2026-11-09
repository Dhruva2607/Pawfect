import React, { useState, useEffect } from 'react';
import { X, CheckCircle2, AlertCircle, Sparkles, ArrowRight, RefreshCw } from 'lucide-react';
import CircularGauge from './CircularGauge';
import { directEval } from '../services/api';

export default function CompatibilityModal({ pet, isOpen, onClose, onContinueAdoption }) {
  if (!isOpen || !pet) return null;

  const [loading, setLoading] = useState(true);
  const [evaluation, setEvaluation] = useState(null);
  const [error, setError] = useState(null);

  // Lifestyle sliders/controls
  const [housingType, setHousingType] = useState('apartment');
  const [hasChildren, setHasChildren] = useState(true);
  const [hasOtherPets, setHasOtherPets] = useState(false);
  const [energyBudget, setEnergyBudget] = useState(3);

  const runEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await directEval({
        session_id: 'web_eval_' + pet._id,
        pet_id: pet._id,
        housing_type: housingType,
        has_children: hasChildren,
        has_other_pets: hasOtherPets,
        energy_budget: energyBudget,
        notes: `Evaluating ${pet.name} for home.`
      });
      setEvaluation(res);
    } catch (err) {
      console.error(err);
      setError('Could not run live AI evaluation. Please verify backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runEvaluation();
  }, [pet]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-white rounded-3xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-stone-200/80 p-6 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-stone-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-stone-900">AI Compatibility Analysis</h3>
              <p className="text-xs text-stone-500">Grounded evaluation for {pet.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center text-stone-600 hover:bg-stone-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="py-5 space-y-5">
          {/* Top Score Showcase */}
          <div className="flex flex-col items-center justify-center py-4 bg-gradient-to-b from-stone-50 to-white rounded-2xl border border-stone-100">
            {loading ? (
              <div className="flex flex-col items-center py-6">
                <RefreshCw className="w-8 h-8 text-amber-500 animate-spin mb-3" />
                <span className="text-xs font-medium text-stone-500">Evaluating grounded lifestyle traits...</span>
              </div>
            ) : evaluation ? (
              <>
                <CircularGauge score={evaluation.compatibility_score} size={110} strokeWidth={9} />
                <h4 className="mt-3 font-semibold text-lg text-stone-900">
                  {evaluation.compatibility_score >= 85 ? 'Exceptional Match' : evaluation.compatibility_score >= 70 ? 'Promising Match' : 'Consideration Needed'}
                </h4>
                <p className="text-xs text-stone-600 text-center max-w-md px-4 mt-1 leading-relaxed">
                  {evaluation.reasoning_summary}
                </p>
              </>
            ) : (
              <p className="text-xs text-rose-500">{error}</p>
            )}
          </div>

          {/* Interactive Lifestyle Preferences Adjuster */}
          <div className="p-4 rounded-2xl bg-stone-50/80 border border-stone-200/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-stone-600">
                Your Lifestyle Parameters
              </span>
              <button
                onClick={runEvaluation}
                disabled={loading}
                className="text-xs text-amber-700 hover:text-amber-800 font-medium flex items-center gap-1"
              >
                <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
                Re-calculate
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div>
                <label className="text-stone-600 block mb-1">Housing</label>
                <select
                  value={housingType}
                  onChange={(e) => setHousingType(e.target.value)}
                  className="w-full bg-white border border-stone-200 rounded-lg p-1.5 text-stone-800 font-medium"
                >
                  <option value="apartment">Apartment</option>
                  <option value="house_with_yard">House & Yard</option>
                </select>
              </div>

              <div>
                <label className="text-stone-600 block mb-1">Children</label>
                <select
                  value={hasChildren ? 'yes' : 'no'}
                  onChange={(e) => setHasChildren(e.target.value === 'yes')}
                  className="w-full bg-white border border-stone-200 rounded-lg p-1.5 text-stone-800 font-medium"
                >
                  <option value="yes">Yes, kids</option>
                  <option value="no">Adults only</option>
                </select>
              </div>

              <div>
                <label className="text-stone-600 block mb-1">Other Pets</label>
                <select
                  value={hasOtherPets ? 'yes' : 'no'}
                  onChange={(e) => setHasOtherPets(e.target.value === 'yes')}
                  className="w-full bg-white border border-stone-200 rounded-lg p-1.5 text-stone-800 font-medium"
                >
                  <option value="no">No other pets</option>
                  <option value="yes">Has pets</option>
                </select>
              </div>

              <div>
                <label className="text-stone-600 block mb-1">Energy Budget</label>
                <select
                  value={energyBudget}
                  onChange={(e) => setEnergyBudget(Number(e.target.value))}
                  className="w-full bg-white border border-stone-200 rounded-lg p-1.5 text-stone-800 font-medium"
                >
                  <option value={1}>1/5 - Chill</option>
                  <option value={2}>2/5 - Relaxed</option>
                  <option value={3}>3/5 - Moderate</option>
                  <option value={4}>4/5 - Active</option>
                  <option value={5}>5/5 - Athlete</option>
                </select>
              </div>
            </div>
          </div>

          {/* Key Insights & Alignment */}
          {evaluation && (
            <div className="space-y-3">
              {/* Pros */}
              <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-200/50">
                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Why this is a strong match
                </div>
                <ul className="text-xs text-stone-700 space-y-1.5">
                  {evaluation.pros?.map((pro, idx) => (
                    <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{pro}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Caveats */}
              {evaluation.caveats?.length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-200/50">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 uppercase tracking-wider mb-2">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    Things to keep in mind
                  </div>
                  <ul className="text-xs text-stone-700 space-y-1.5">
                    {evaluation.caveats?.map((caveat, idx) => (
                      <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{caveat}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-stone-100 flex items-center gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 text-xs font-medium text-stone-600 hover:bg-stone-100 rounded-xl transition-colors"
          >
            Close
          </button>
          <button
            onClick={() => {
              onClose();
              onContinueAdoption(pet);
            }}
            className="flex-1 py-2.5 px-4 text-xs font-medium text-white bg-stone-900 hover:bg-stone-800 rounded-xl transition-colors flex items-center justify-center gap-1.5 shadow-sm"
          >
            Continue to Adoption
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
