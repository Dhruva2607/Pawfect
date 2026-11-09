import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { streamChatMessage } from '../services/api';
import CircularGauge from './CircularGauge';

export default function ChatCounselor({ onViewPet, onAdoptPet }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I am your AI Pet Adoption Counselor at PawFect. 🐾\nTell me about your lifestyle—do you live in an apartment or house? Any children, resident pets, or daily walking routines?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [quickReplies, setQuickReplies] = useState([
    'Apartment with kids',
    'Quiet home, looking for a cat',
    'Active house with a yard',
    'Low shedding / hypoallergenic'
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
  }, [messages, isTyping]);

  const handleSend = async (messageText) => {
    const text = messageText || input;
    if (!text.trim() || isTyping) return;

    setInput('');
    setQuickReplies([]);

    const userMsgId = 'usr_' + Date.now();
    const botMsgId = 'bot_' + (Date.now() + 1);

    // Append user message and prepare empty bot streaming placeholder
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: text },
      { id: botMsgId, role: 'assistant', content: '', isStreaming: true }
    ]);
    setIsTyping(true);

    await streamChatMessage({
      sessionId,
      message: text,
      onTyping: () => {
        setIsTyping(true);
      },
      onToken: (token) => {
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
        if (data.candidate_matches) setTopMatches(data.candidate_matches);
        if (data.evaluations) setEvaluations(data.evaluations);
      },
      onDone: (data) => {
        setIsTyping(false);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId ? { ...msg, isStreaming: false } : msg
          )
        );
      },
      onError: (err) => {
        setIsTyping(false);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  content:
                    msg.content ||
                    'I encountered an issue connecting to the AI counselor backend. Please ensure the FastAPI server is running.',
                  isStreaming: false
                }
              : msg
          )
        );
      }
    });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] max-w-4xl mx-auto px-4 py-4 sm:py-6">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-4 border-b border-stone-200/60 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600">
            <Sparkles className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h2 className="font-semibold text-stone-900 leading-tight">AI Adoption Counselor</h2>
            <p className="text-xs text-stone-600">
              {isTyping ? 'Analyzing lifestyle constraints...' : 'LangGraph + Gemini stateful counseling'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/50">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Live SSE
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
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
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  isUser
                    ? 'bg-stone-900 text-white shadow-sm'
                    : 'bg-white border border-stone-200/70 text-stone-800 shadow-sm'
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
            <div className="bg-white border border-stone-200/70 rounded-2xl px-4 py-3 shadow-sm flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce" />
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce [animation-delay:0.2s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}

        {/* Top Matches Showcase Cards */}
        {topMatches.length > 0 && evaluations.length > 0 && (
          <div className="pt-3 pb-2 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-stone-600">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              Top Compatibility Recommendations
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {evaluations.map((evalItem) => {
                const pet = topMatches.find((p) => p._id === evalItem.pet_id) || {
                  _id: evalItem.pet_id,
                  name: evalItem.pet_name,
                  breed: 'Companion',
                  photo_url: 'https://images.unsplash.com/photo-1552053831-71594a27632d'
                };

                return (
                  <div
                    key={evalItem.pet_id}
                    className="bg-white rounded-2xl border border-stone-200/80 p-4 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <img
                            src={pet.photo_url || 'https://images.unsplash.com/photo-1552053831-71594a27632d'}
                            alt={evalItem.pet_name}
                            className="w-12 h-12 rounded-xl object-cover"
                          />
                          <div>
                            <h4 className="font-semibold text-stone-900 leading-tight">
                              {evalItem.pet_name}
                            </h4>
                            <p className="text-xs text-stone-500">{pet.breed}</p>
                          </div>
                        </div>
                        <CircularGauge score={evalItem.compatibility_score} size={50} strokeWidth={5} />
                      </div>

                      {/* Pros & Caveats */}
                      <div className="mt-3 space-y-1.5 text-xs">
                        {evalItem.pros?.slice(0, 2).map((pro, idx) => (
                          <div key={idx} className="flex items-start gap-1.5 text-stone-700">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                            <span>{pro}</span>
                          </div>
                        ))}
                        {evalItem.caveats?.slice(0, 1).map((caveat, idx) => (
                          <div key={idx} className="flex items-start gap-1.5 text-amber-700">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                            <span>{caveat}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-stone-100 flex items-center gap-2">
                      <button
                        onClick={() => onViewPet(pet)}
                        className="flex-1 py-1.5 px-3 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200/70 rounded-lg transition-colors"
                      >
                        Profile
                      </button>
                      <button
                        onClick={() => onAdoptPet(pet)}
                        className="flex-1 py-1.5 px-3 text-xs font-medium text-white bg-stone-900 hover:bg-stone-800 rounded-lg transition-colors flex items-center justify-center gap-1"
                      >
                        Adopt
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Replies */}
      {quickReplies.length > 0 && (
        <div className="flex flex-wrap gap-2 py-2">
          {quickReplies.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              className="text-xs font-medium px-3 py-1.5 rounded-full bg-white border border-stone-300/80 text-stone-700 hover:border-amber-500 hover:text-amber-800 hover:bg-amber-50/50 transition-all shadow-2xs"
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
        className="mt-2 relative flex items-center"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your home, lifestyle, kids, or energy..."
          disabled={isTyping}
          className="w-full bg-white border border-stone-200/80 rounded-2xl pl-4 pr-12 py-3.5 text-sm text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 shadow-sm transition-all"
        />
        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="absolute right-2.5 w-9 h-9 rounded-xl bg-stone-900 hover:bg-stone-800 disabled:opacity-30 disabled:hover:bg-stone-900 text-white flex items-center justify-center transition-all shadow-sm"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
