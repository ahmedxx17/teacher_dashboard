import React from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import { Clock, Layers, Users, Globe } from 'lucide-react';

export const GenerationControls = () => {
  const {
    periodLength,
    setPeriodLength,
    numLessons,
    setNumLessons,
    studentLevel,
    setStudentLevel,
    outputLanguage,
    setOutputLanguage,
  } = useCurriculumStore();

  return (
    <div className="mt-5 pt-5 border-t border-slate-100">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Lesson & Pedagogy Settings
        </span>
        <span className="text-[11px] text-slate-400">
          Customizes pacing, difficulty, and language
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Period Length */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="period-length-select"
            className="text-xs font-medium text-slate-700 flex items-center gap-1.5"
          >
            <Clock className="w-3.5 h-3.5 text-brand-600" />
            <span>Period Length</span>
          </label>
          <select
            id="period-length-select"
            value={periodLength}
            onChange={(e) => setPeriodLength(Number(e.target.value))}
            className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value={30}>30 Minutes</option>
            <option value={40}>40 Minutes (Standard)</option>
            <option value={45}>45 Minutes</option>
            <option value={60}>60 Minutes</option>
          </select>
        </div>

        {/* 2. Number of Lessons */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="num-lessons-input"
            className="text-xs font-medium text-slate-700 flex items-center gap-1.5"
          >
            <Layers className="w-3.5 h-3.5 text-brand-600" />
            <span>Number of Lessons</span>
          </label>
          <input
            id="num-lessons-input"
            type="number"
            min={1}
            max={10}
            value={numLessons}
            onChange={(e) => {
              const val = Math.max(1, Math.min(10, Number(e.target.value) || 1));
              setNumLessons(val);
            }}
            className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
        </div>

        {/* 3. Student Level */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="student-level-select"
            className="text-xs font-medium text-slate-700 flex items-center gap-1.5"
          >
            <Users className="w-3.5 h-3.5 text-brand-600" />
            <span>Student Level</span>
          </label>
          <select
            id="student-level-select"
            value={studentLevel}
            onChange={(e) => setStudentLevel(e.target.value)}
            className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="Weak">Weak (Foundational Support)</option>
            <option value="Average">Average (Balanced)</option>
            <option value="Strong">Strong (Advanced / Challenging)</option>
          </select>
        </div>

        {/* 4. Output Language */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="output-language-select"
            className="text-xs font-medium text-slate-700 flex items-center gap-1.5"
          >
            <Globe className="w-3.5 h-3.5 text-brand-600" />
            <span>Output Language</span>
          </label>
          <select
            id="output-language-select"
            value={outputLanguage}
            onChange={(e) => setOutputLanguage(e.target.value)}
            className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="English">English</option>
            <option value="English + Urdu key terms">English + Urdu key terms</option>
          </select>
        </div>
      </div>
    </div>
  );
};
