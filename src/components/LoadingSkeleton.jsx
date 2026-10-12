import React from 'react';
import { Sparkles } from 'lucide-react';

export const LoadingSkeleton = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-slate-100 shadow-sm">
        <div className="space-y-2.5 max-w-lg w-full">
          <div className="h-4 bg-slate-200 rounded w-1/3"></div>
          <div className="h-7 bg-slate-200 rounded-lg w-3/4"></div>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-9 w-28 bg-slate-200 rounded-xl"></div>
          <div className="h-9 w-28 bg-slate-200 rounded-xl"></div>
        </div>
      </div>

      {/* Generating Banner */}
      <div className="flex items-center gap-3 p-4 bg-emerald-50/70 border border-emerald-200/60 rounded-2xl text-brand-800 text-sm font-medium">
        <Sparkles className="w-5 h-5 text-brand-600 animate-spin" />
        <span>Gemini AI is crafting a tailored lesson outline strictly from official textbook content...</span>
      </div>

      {/* Grid of Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Objectives Skeleton */}
        <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/2"></div>
          <div className="space-y-2.5">
            <div className="h-4 bg-slate-100 rounded w-full"></div>
            <div className="h-4 bg-slate-100 rounded w-5/6"></div>
            <div className="h-4 bg-slate-100 rounded w-4/6"></div>
          </div>
        </div>

        {/* Key Concepts Skeleton */}
        <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/2"></div>
          <div className="space-y-3">
            <div className="h-14 bg-slate-100 rounded-xl"></div>
            <div className="h-14 bg-slate-100 rounded-xl"></div>
          </div>
        </div>
      </div>

      {/* Timeline Skeleton */}
      <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-5">
        <div className="h-6 bg-slate-200 rounded w-1/3"></div>
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-4">
              <div className="w-16 h-8 bg-slate-200 rounded-lg shrink-0"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-200 rounded w-1/4"></div>
                <div className="h-4 bg-slate-100 rounded w-full"></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Activities & Check Questions Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-3">
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
          <div className="h-4 bg-slate-100 rounded w-full"></div>
          <div className="h-4 bg-slate-100 rounded w-5/6"></div>
        </div>
        <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-3">
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
          <div className="h-4 bg-slate-100 rounded w-full"></div>
          <div className="h-4 bg-slate-100 rounded w-5/6"></div>
        </div>
      </div>
    </div>
  );
};
