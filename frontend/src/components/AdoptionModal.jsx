import React, { useState } from 'react';
import { X, CheckCircle2, PartyPopper, Check, ArrowRight } from 'lucide-react';
import { applyAdoption } from '../services/api';

const STAGES = [
  { id: 'match', label: 'Match', index: 0 },
  { id: 'review', label: 'Review', index: 1 },
  { id: 'apply', label: 'Apply', index: 2 },
  { id: 'adopt', label: 'Adopt', index: 3 },
];

export default function AdoptionModal({ pet, isOpen, onClose }) {
  if (!isOpen || !pet) return null;

  const [currentStage, setCurrentStage] = useState('apply');
  const [formData, setFormData] = useState({
    name: 'Jane Doe',
    email: 'jane.doe@example.com',
    phone: '555-0199',
    housing: '2-bedroom apartment with secure balcony',
    household: '1 adult, 1 child (6 yrs)',
    notes: `We are thrilled to welcome ${pet.name} to our family!`
  });
  const [submitting, setSubmitting] = useState(false);
  const [submittedResult, setSubmittedResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await applyAdoption({
        user_id: 'user_default',
        pet_id: pet._id,
        applicant_name: formData.name,
        applicant_email: formData.email,
        applicant_phone: formData.phone,
        housing_details: formData.housing,
        household_members: formData.household,
        notes: formData.notes
      });
      setSubmittedResult(res);
      setCurrentStage('apply');
    } catch (err) {
      console.error(err);
      setError('Could not submit application. Please ensure backend is running.');
    } finally {
      setSubmitting(false);
    }
  };

  const getStageIndex = (stage) => {
    return STAGES.findIndex(s => s.id === stage);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-white rounded-3xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-stone-200/80 p-6 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-stone-100">
          <div>
            <h3 className="font-bold text-stone-900 text-lg">Adoption Journey</h3>
            <p className="text-xs text-stone-500">Applying for {pet.name} ({pet.breed})</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center text-stone-600 hover:bg-stone-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 4-Stage Horizontal Stepper [FROM MARKDOWN: Screen 7] */}
        <div className="py-6 border-b border-stone-100">
          <div className="flex items-center justify-between relative">
            {STAGES.map((step, idx) => {
              const activeIdx = submittedResult ? 2 : 1;
              const isPassed = idx < activeIdx;
              const isCurrent = idx === activeIdx;

              return (
                <div key={step.id} className="flex-1 flex flex-col items-center relative z-10">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      isPassed
                        ? 'bg-emerald-500 text-white shadow-sm'
                        : isCurrent
                        ? 'bg-amber-500 text-white ring-4 ring-amber-100 shadow-sm'
                        : 'bg-stone-100 text-stone-400'
                    }`}
                  >
                    {isPassed ? <Check className="w-4 h-4" /> : idx + 1}
                  </div>
                  <span
                    className={`text-[11px] font-medium mt-1.5 ${
                      isCurrent
                        ? 'text-amber-800 font-semibold'
                        : isPassed
                        ? 'text-stone-700'
                        : 'text-stone-400'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}

            {/* Background line */}
            <div className="absolute top-4 left-6 right-6 h-0.5 bg-stone-200 -z-0" />
          </div>
        </div>

        {/* Body content */}
        <div className="py-5">
          {submittedResult ? (
            /* Celebration state [FROM MARKDOWN: Screen 7] */
            <div className="py-6 flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-2xl animate-bounce">
                🎉
              </div>
              <div>
                <h4 className="text-xl font-bold text-stone-900">Application Submitted!</h4>
                <p className="text-xs text-stone-600 max-w-sm mt-1 leading-relaxed">
                  Your application for <span className="font-semibold text-stone-900">{pet.name}</span> has been securely transmitted. Shelter staff will review your lifestyle alignment and get in touch within 24 hours.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-stone-50 border border-stone-200 text-xs font-mono text-stone-600">
                Application ID: {submittedResult.application_id}
              </div>

              <button
                onClick={onClose}
                className="mt-4 px-6 py-2.5 bg-stone-900 hover:bg-stone-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
              >
                Done
              </button>
            </div>
          ) : (
            /* Adoption Application Form */
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-stone-700 block mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-stone-700 block mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-stone-700 block mb-1">Phone Number</label>
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-stone-700 block mb-1">Household Members</label>
                  <input
                    type="text"
                    value={formData.household}
                    onChange={(e) => setFormData({ ...formData, household: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-stone-700 block mb-1">Home & Yard Description</label>
                <input
                  type="text"
                  value={formData.housing}
                  onChange={(e) => setFormData({ ...formData, housing: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-stone-700 block mb-1">Message to Shelter Staff</label>
                <textarea
                  rows={2}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              {/* Submit Buttons */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2.5 px-4 text-xs font-medium text-stone-600 hover:bg-stone-100 rounded-xl transition-colors"
                >
                  Save for Later
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 py-2.5 px-4 text-xs font-semibold text-white bg-stone-900 hover:bg-stone-800 disabled:opacity-50 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2"
                >
                  {submitting ? 'Submitting...' : 'Submit Application 🚀'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

