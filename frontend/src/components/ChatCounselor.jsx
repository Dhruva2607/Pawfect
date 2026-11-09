import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User, ArrowRight, CheckCircle2, AlertCircle, Compass, RefreshCw } from 'lucide-react';
import { streamChatMessage } from '../services/api';
import { SAMPLE_PETS } from '../data/samplePets';
import CircularGauge from './CircularGauge';

export default function ChatCounselor({
  onViewPet,
  onAdoptPet,
  onUnlockCatalog,
  hasCompletedIntake = false,
  user = null
}) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello ${user?.name ? user.name.split(' ')[0] : 'there'}! I am your AI Pet Adoption Counselor at PawFect. 🐾\n\nTo find your dream companion, I need to understand your lifestyle first:\n• Do you live in an apartment or a house with a yard?\n• Any kids or resident pets?\n• What's your daily schedule or energy preference?`
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [quickReplies, setQuickReplies] = useState([
    'Apartment with kids 🐶',
    'Quiet home, looking for a cat 🐱',
    'Active house with a yard 🏃‍♂️',
    'Low shedding / hypoallergenic ✨'
  ]);
  const [topMatches, setTopMatches] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 9));

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, topMatches]);

  // Local simulated fallback in case FastAPI backend or MongoDB is offline
  const generateLocalAiFallback = (userText) => {
    const lower = userText.toLowerCase();
    const wantsCat = lower.includes('cat') || lower.includes('feline');
    const wantsDog = lower.includes('dog') || lower.includes('pup') || lower.includes('hound');
    const isApartment = lower.includes('apartment') || lower.includes('condo') || lower.includes('flat');
    const hasKids = lower.includes('kid') || lower.includes('child') || lower.includes('family');

    let pool = SAMPLE_PETS;
    if (wantsCat && !wantsDog) {
      pool = SAMPLE_PETS.filter(p => p.species === 'cat');
    } else if (wantsDog && !wantsCat) {
      pool = SAMPLE_PETS.filter(p => p.species === 'dog');
    }
    if (hasKids) {
      pool = pool.filter(p => p.good_with_kids);
    }
    if (pool.length === 0) pool = SAMPLE_PETS.slice(0, 3);

    const candidates = pool.slice(0, 3);
    const evals = candidates.map((p, idx) => ({
      pet_id: p._id || p.id,
      pet_name: p.name,
      compatibility_score: 95 - idx * 4,
      pros: [
        `Energy level (${p.energy_level}/5) aligns with your daily routine`,
        p.good_with_kids ? 'Excellent and patient with family members' : 'Affectionate and loyal companion'
      ],
      caveats: [
        p.exercise_needs || 'Requires consistent daily outdoor stimulation'
      ],
      reasoning_summary: `${p.name} is a wonderful match for your home environment.`
    }));

    const responseMsg = `I analyzed your lifestyle and found ${candidates.length} exceptional companion matches! Based on your living space and household dynamics, ${candidates[0].name} (${candidates[0].breed}) stands out as your highest alignment match.`;

    return { responseMsg, candidates, evals, quickReplies: ['View compatibility breakdown', 'Looking for lower energy', 'Explore all shelter pets'] };
  };

  const handleSend = async (messageText) => {
    const text = messageText || input;
    if (!text.trim() || isTyping) return;

    setInput('');
    setQuickReplies([]);

    const userMsgId = 'usr_' + Date.now();
    const botMsgId = 'bot_' + (Date.now() + 1);

    // Append user message & placeholder
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: text },
      { id: botMsgId, role: 'assistant', content: '', isStreaming: true }
    ]);
    setIsTyping(true);

    let receivedTokens = false;

    try {
      await streamChatMessage({
        sessionId,
        message: text,
        userId: user?.user_id || user?.id || 'user_default',
        onTyping: () => {
          setIsTyping(true);
        },
        onToken: (token) => {
          receivedTokens = true;
          setIsTyping(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId ? { ...msg, content: msg.content + token } : msg
            )
          );
        },
        onQuickReplies: (replies) => {
          if (replies && replies.length > 0) setQuickReplies(replies);
        },
        onMatches: (data) => {
          if (!data) return;
          const candidates = data.candidate_matches || data.matches || [];
          const evals = data.evaluations || [];
          if (candidates.length > 0) setTopMatches(candidates);
          if (evals.length > 0) setEvaluations(evals);
          if (candidates.length > 0 && onUnlockCatalog) {
            onUnlockCatalog(candidates);
          }
        },
        onDone: (data) => {
          setIsTyping(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId
                ? {
                    ...msg,
                    content: data?.response_message || msg.content,
                    isStreaming: false
                  }
                : msg
            )
          );
        },
        onError: (err) => {
          console.warn('Backend SSE streaming unavailable, running local counselor engine:', err);
          // Fall back gracefully to local engine so user is never blocked
          const fallback = generateLocalAiFallback(text);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId
                ? { ...msg, content: fallback.responseMsg, isStreaming: false }
                : msg
            )
          );
          setTopMatches(fallback.candidates);
          setEvaluations(fallback.evals);
          setQuickReplies(fallback.quickReplies);
          setIsTyping(false);
          if (onUnlockCatalog) onUnlockCatalog(fallback.candidates);
        }
      });
    } catch (e) {
      console.warn('Fetch failed, switching to local intelligence:', e);
      const fallback = generateLocalAiFallback(text);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMsgId
            ? { ...msg, content: fallback.responseMsg, isStreaming: false }
            : msg
        )
      );
      setTopMatches(fallback.candidates);
      setEvaluations(fallback.evals);
      setQuickReplies(fallback.quickReplies);
      setIsTyping(false);
      if (onUnlockCatalog) onUnlockCatalog(fallback.candidates);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-4xl mx-auto px-2 sm:px-4">
      {/* Step Indicator Header Banner */}
      <div className="mb-4 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20 rounded-2xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold text-sm shadow-xs">
            1
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-900">
              Step 1: AI Lifestyle Counseling
            </h3>
            <p className="text-xs text-stone-600">
              Share your living space and schedule to unlock your personalized pet matches.
            </p>
          </div>
        </div>

        {topMatches.length > 0 ? (
          <button
            onClick={() => onUnlockCatalog && onUnlockCatalog(topMatches, true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold shadow-xs transition-all self-start sm:self-auto"
          >
            <Compass className="w-3.5 h-3.5 text-amber-400" />
            <span>Explore All Pets ({SAMPLE_PETS.length}+)</span>
            <ArrowRight className="w-3 h-3 ml-0.5" />
          </button>
        ) : (
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-stone-500 bg-white/80 px-2.5 py-1 rounded-lg border border-stone-200">
            <span>🔒 Catalog unlocks after intake</span>
          </div>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 sm:pr-2">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-semibold ${
                  isUser
                    ? 'bg-stone-900 text-white'
                    : 'bg-amber-100 text-amber-800 border border-amber-200/60'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[85%] sm:max-w-[78%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap ${
                  isUser
                    ? 'bg-stone-900 text-white rounded-tr-xs'
                    : 'bg-white border border-stone-200/80 text-stone-800 rounded-tl-xs shadow-2xs'
                }`}
              >
                {msg.content}
                {msg.isStreaming && (
                  <span className="inline-block w-1.5 h-4 ml-1 bg-amber-500 animate-pulse align-middle" />
                )}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-amber-100 border border-amber-200/60 flex items-center justify-center text-amber-800 shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-white border border-stone-200/70 rounded-2xl px-4 py-3 shadow-2xs flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce" />
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce [animation-delay:0.2s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}

        {/* Top Matches Showcase Cards */}
        {topMatches.length > 0 && (
          <div className="pt-3 pb-2 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-stone-700">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                AI Top Compatibility Matches
              </div>
              <span className="text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium border border-emerald-200/50">
                Intake Complete
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {topMatches.map((pet, idx) => {
                const evalItem = evaluations.find(
                  (e) => e.pet_id === pet._id || e.pet_id === pet.id
                ) || {
                  compatibility_score: 94 - idx * 4,
                  pros: [`Energy level (${pet.energy_level}/5) fits your space`, 'Gentle and well-adjusted'],
                  caveats: [pet.exercise_needs || 'Daily walk routine required']
                };

                return (
                  <div
                    key={pet._id || pet.id || idx}
                    className="bg-white rounded-2xl border border-stone-200/90 p-4 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <img
                            src={pet.photo_url || 'https://images.unsplash.com/photo-1552053831-71594a27632d'}
                            alt={pet.name}
                            className="w-12 h-12 rounded-xl object-cover"
                          />
                          <div>
                            <h4 className="font-bold text-stone-900 leading-tight">
                              {pet.name}
                            </h4>
                            <p className="text-xs text-stone-500">{pet.breed} • {pet.species === 'dog' ? '🐶 Dog' : '🐱 Cat'}</p>
                          </div>
                        </div>
                        <CircularGauge score={evalItem.compatibility_score} size={48} strokeWidth={4.5} />
                      </div>

                      {/* Pros & Caveats */}
                      <div className="mt-3 space-y-1 text-xs">
                        {evalItem.pros?.slice(0, 2).map((pro, pIdx) => (
                          <div key={pIdx} className="flex items-start gap-1.5 text-stone-700">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                            <span className="line-clamp-1">{pro}</span>
                          </div>
                        ))}
                        {evalItem.caveats?.slice(0, 1).map((caveat, cIdx) => (
                          <div key={cIdx} className="flex items-start gap-1.5 text-amber-700">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                            <span className="line-clamp-1">{caveat}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-stone-100 flex items-center gap-2">
                      <button
                        onClick={() => onViewPet(pet)}
                        className="flex-1 py-1.5 px-3 text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200/70 rounded-xl transition-colors"
                      >
                        Profile
                      </button>
                      <button
                        onClick={() => onAdoptPet(pet)}
                        className="flex-1 py-1.5 px-3 text-xs font-semibold text-white bg-stone-900 hover:bg-stone-800 rounded-xl transition-colors flex items-center justify-center gap-1 shadow-xs"
                      >
                        Adopt
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Unlocked Catalog Banner */}
            <div className="mt-3 p-3.5 rounded-2xl bg-stone-900 text-white flex items-center justify-between gap-3 shadow-sm">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">🎉</span>
                <div>
                  <h4 className="font-bold text-xs">Full Pet Catalog Unlocked!</h4>
                  <p className="text-[11px] text-stone-400">You can now explore all shelter pets or apply for your top matches.</p>
                </div>
              </div>
              <button
                onClick={() => onUnlockCatalog && onUnlockCatalog(topMatches, true)}
                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition-colors whitespace-nowrap flex items-center gap-1 shadow-xs"
              >
                <span>Browse All</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Replies */}
      {quickReplies.length > 0 && (
        <div className="flex flex-wrap gap-2 py-2 mt-1">
          {quickReplies.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              className="text-xs font-medium px-3 py-1.5 rounded-full bg-white border border-stone-300 text-stone-700 hover:border-amber-500 hover:text-amber-800 hover:bg-amber-50/50 transition-all shadow-2xs"
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="mt-1 relative flex items-center"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your home, children, other pets, energy level..."
          className="w-full pl-4 pr-12 py-3 bg-white border border-stone-200/90 rounded-2xl text-xs sm:text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 text-stone-800 shadow-2xs"
        />
        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="absolute right-2 w-8 h-8 rounded-xl bg-stone-900 text-white flex items-center justify-center hover:bg-stone-800 disabled:opacity-40 disabled:hover:bg-stone-900 transition-all shadow-xs"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
