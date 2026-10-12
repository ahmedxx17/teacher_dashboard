import React from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import { BookOpen, Loader2 } from 'lucide-react';

export const SubjectSelect = () => {
  const {
    subjects,
    selectedSubject,
    selectSubject,
    isLoadingSubjects,
  } = useCurriculumStore();

  return (
    <div className="flex flex-col gap-1.5 w-full">
      <label
        htmlFor="subject-select"
        className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5"
      >
        <BookOpen className="w-4 h-4 text-brand-600" />
        <span>1. Select Subject</span>
      </label>
      <div className="relative">
        <select
          id="subject-select"
          value={selectedSubject}
          onChange={(e) => selectSubject(e.target.value)}
          disabled={isLoadingSubjects || subjects.length === 0}
          className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-4 py-3 pr-10 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400"
        >
          <option value="">
            {isLoadingSubjects
              ? 'Loading subjects...'
              : subjects.length === 0
              ? 'No subjects found (Run import_book.py)'
              : 'Choose a Subject & Class...'}
          </option>
          {subjects.map((sub) => (
            <option key={sub.id} value={sub.id}>
              {sub.name} — Class {sub.class} ({sub.medium === 'ur' ? 'Urdu Medium' : 'English Medium'})
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400">
          {isLoadingSubjects ? (
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
