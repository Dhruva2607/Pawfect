import React from 'react';

export default function CircularGauge({ score = 95, size = 80, strokeWidth = 7 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const colorClass = score >= 85 
    ? 'text-emerald-500 stroke-emerald-500' 
    : score >= 70 
    ? 'text-amber-500 stroke-amber-500' 
    : 'text-rose-500 stroke-rose-500';

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="w-full h-full transform -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className="stroke-stone-200/80"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Animated value arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          className={`${colorClass} transition-all duration-1000 ease-out`}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className={`font-bold tracking-tight ${colorClass.split(' ')[0]}`} style={{ fontSize: size * 0.28 }}>
          {score}%
        </span>
        <span className="text-[10px] uppercase font-semibold text-stone-600 tracking-wider">
          Match
        </span>
      </div>
    </div>
  );
}
