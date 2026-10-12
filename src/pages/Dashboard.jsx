import React, { useEffect } from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import { SubjectSelect } from '../components/SubjectSelect';
import { ChapterSelect } from '../components/ChapterSelect';
import { TopicSelect } from '../components/TopicSelect';
import { OutlineView } from '../components/OutlineView';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ErrorBanner } from '../components/ErrorBanner';
import {
  Sparkles,
  GraduationCap,
  BookOpen,
  ArrowRight,
  Database,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';

export const Dashboard = () => {
  const {
    loadSubjects,
    selectedSubject,
    selectedChapter,
    selectedTopic,
    outline,
    outlineMeta,
    isGeneratingOutline,
    generateOutline,
  } = useCurriculumStore();

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  const canGenerate = Boolean(selectedTopic) && !isGeneratingOutline;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between py-3">
          <div className="flex items-center gap-3.5">
            <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-white shadow-md shadow-brand-500/20">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900">
                  Teacher Dashboard
                </h1>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-brand-100 text-brand-800">
                  Class 9 & 10
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Punjab Curriculum & Textbook Board (PCTB) • AI Lesson Planning
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 font-medium">
              <BookOpen className="w-3.5 h-3.5 text-slate-600" />
              English Medium Books
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">
        {/* Selection Card (Dependent Dropdowns + Action Button) */}
        <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-sm">
          <div className="mb-6">
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              Plan Your Next Class
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Select your subject, chapter, and topic to generate a comprehensive, curriculum-aligned lesson outline.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <SubjectSelect />
            <ChapterSelect />
            <TopicSelect />
          </div>

          {/* Action Row */}
          <div className="mt-6 pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-500 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-brand-600" />
              <span>Outlines are cached locally. Each topic is processed by AI once.</span>
            </div>

            <button
              onClick={() => generateOutline(false)}
              disabled={!canGenerate}
              className={`w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-2xl font-semibold text-sm transition-all shadow-md active:scale-95 ${
                canGenerate
                  ? 'bg-brand-600 hover:bg-brand-700 text-white shadow-brand-600/25 hover:shadow-brand-600/35'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed shadow-none'
              }`}
            >
              <Sparkles className={`w-4 h-4 ${isGeneratingOutline ? 'animate-spin' : ''}`} />
              <span>
                {isGeneratingOutline
                  ? 'Generating Outline...'
                  : outline
                  ? 'Outline Loaded (Click to Re-fetch)'
                  : 'Generate Outline'}
              </span>
              {!isGeneratingOutline && canGenerate && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        <ErrorBanner />

        {/* Dynamic Display Area: Loading -> Outline -> Empty State */}
        {isGeneratingOutline ? (
          <LoadingSkeleton />
        ) : outline ? (
          <OutlineView />
        ) : (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-white/60 p-10 sm:p-14 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 mb-4">
              <BookOpen className="h-7 w-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 mb-1">
              No Lesson Outline Selected
            </h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
              Pick your Subject, Chapter, and Topic from the dropdowns above and click{' '}
              <strong className="text-slate-700 font-semibold">"Generate Outline"</strong> to get a classroom-ready 40-45 minute lesson plan.
            </p>
            <div className="inline-flex items-center gap-6 text-xs text-slate-400 font-medium">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-brand-500"></span>
                Official PCTB Textbooks
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                Cached in Postgres
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                Zero Latency on Cache Hit
              </span>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© {new Date().getFullYear()} Teacher Dashboard — Built for High School Teachers in Pakistan</p>
          <p className="flex items-center gap-1">
            <span>Powered by Gemini API & Supabase Edge Functions</span>
          </p>
        </div>
      </footer>
    </div>
  );
};
