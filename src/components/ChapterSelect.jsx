import React from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import { Layers, Loader2 } from 'lucide-react';

export const ChapterSelect = () => {
  const {
    chapters,
    selectedSubject,
    selectedChapter,
    selectChapter,
    isLoadingChapters,
  } = useCurriculumStore();

  const isDisabled = !selectedSubject || isLoadingChapters;

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <label
        htmlFor="chapter-select"
        className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5"
      >
        <Layers className="w-4 h-4 text-brand-600" />
        <span>2. Select Chapter / Unit</span>
      </label>
      <div className="relative">
        <select
          id="chapter-select"
          value={selectedChapter}
          onChange={(e) => selectChapter(e.target.value)}
          disabled={isDisabled}
          className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-4 py-3 pr-10 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 disabled:cursor-not-allowed disabled:bg-slate-100/70 disabled:text-slate-400"
        >
          <option value="">
            {!selectedSubject
              ? 'First select a subject above'
              : isLoadingChapters
              ? 'Loading chapters...'
              : chapters.length === 0
              ? 'No chapters in this subject'
              : 'Choose a Chapter...'}
          </option>
          {chapters.map((chap) => (
            <option key={chap.id} value={chap.id}>
              Chapter {chap.number}: {chap.title}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400">
          {isLoadingChapters ? (
            <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </div>
      </div>
    </div>
  );
};
