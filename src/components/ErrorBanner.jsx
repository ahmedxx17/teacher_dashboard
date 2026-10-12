import React from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import { AlertCircle, RotateCcw, X } from 'lucide-react';

export const ErrorBanner = () => {
  const { error, clearError, generateOutline, isGeneratingOutline } = useCurriculumStore();

  if (!error) return null;

  return (
    <div className="rounded-2xl border border-red-200 bg-red-50/90 p-4 sm:p-5 shadow-sm text-red-900 transition-all">
      <div className="flex items-start gap-3.5">
        <div className="rounded-full bg-red-100 p-2 text-red-600 shrink-0">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div className="flex-1 space-y-1">
          <h4 className="text-sm font-semibold text-red-950">Something went wrong</h4>
          <p className="text-sm text-red-800 leading-relaxed">{error}</p>
          <div className="pt-2 flex items-center gap-3">
            <button
              onClick={() => generateOutline(false)}
              disabled={isGeneratingOutline}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-red-600 text-white hover:bg-red-700 transition disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
            <button
              onClick={clearError}
              className="text-xs text-red-700 hover:text-red-900 font-medium underline underline-offset-2"
            >
              Dismiss
            </button>
          </div>
        </div>
        <button
          onClick={clearError}
          className="text-red-400 hover:text-red-600 p-1 rounded-lg transition"
          aria-label="Close error banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
