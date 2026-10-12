import React, { useState } from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import {
  Copy,
  Check,
  RotateCw,
  Clock,
  Target,
  BookOpen,
  Sparkles,
  HelpCircle,
  Activity,
  Database,
  ChevronRight,
  Zap,
} from 'lucide-react';

export const OutlineView = () => {
  const {
    outline,
    outlineMeta,
    subjects,
    chapters,
    topics,
    selectedSubject,
    selectedChapter,
    selectedTopic,
    generateOutline,
    isGeneratingOutline,
  } = useCurriculumStore();

  const [copied, setCopied] = useState(false);

  if (!outline) return null;

  // Resolve breadcrumb entities
  const currentSubject = subjects.find((s) => s.id === selectedSubject);
  const currentChapter = chapters.find((c) => c.id === selectedChapter);
  const currentTopic = topics.find((t) => t.id === selectedTopic);

  // Compute total lesson duration
  const totalMinutes = Array.isArray(outline.lesson_flow)
    ? outline.lesson_flow.reduce((acc, step) => acc + (Number(step.duration_minutes) || 0), 0)
    : 45;

  // Format outline as readable plain text / markdown for clipboard copying
  const formatAsPlainText = () => {
    let text = `LESSON OUTLINE: ${outline.title || currentTopic?.title}\n`;
    if (currentSubject) text += `Subject: ${currentSubject.name} (Class ${currentSubject.class})\n`;
    if (currentChapter) text += `Chapter ${currentChapter.number}: ${currentChapter.title}\n`;
    text += `Duration: ${totalMinutes} Minutes\n\n`;

    if (outline.learning_objectives?.length) {
      text += `=== LEARNING OBJECTIVES ===\n`;
      outline.learning_objectives.forEach((obj, idx) => {
        text += `${idx + 1}. ${obj}\n`;
      });
      text += `\n`;
    }

    if (outline.key_concepts?.length) {
      text += `=== KEY CONCEPTS & DEFINITIONS ===\n`;
      outline.key_concepts.forEach((concept) => {
        text += `• ${concept.term}: ${concept.explanation}\n`;
      });
      text += `\n`;
    }

    if (outline.lesson_flow?.length) {
      text += `=== LESSON FLOW TIMELINE (${totalMinutes} mins) ===\n`;
      outline.lesson_flow.forEach((step, idx) => {
        text += `${idx + 1}. [${step.duration_minutes}m] ${step.step}\n   ${step.details}\n`;
      });
      text += `\n`;
    }

    if (outline.activities?.length) {
      text += `=== CLASSROOM ACTIVITIES ===\n`;
      outline.activities.forEach((act, idx) => {
        text += `${idx + 1}. ${act}\n`;
      });
      text += `\n`;
    }

    if (outline.check_questions?.length) {
      text += `=== ASSESSMENT / CHECK QUESTIONS ===\n`;
      outline.check_questions.forEach((q, idx) => {
        text += `Q${idx + 1}: ${q}\n`;
      });
    }

    return text;
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formatAsPlainText());
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Card with Breadcrumb & Action Controls */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        {/* Breadcrumb Navigation */}
        <nav className="flex flex-wrap items-center gap-1.5 text-xs font-medium text-slate-500 mb-4">
          <span className="flex items-center gap-1 text-slate-700">
            <BookOpen className="w-3.5 h-3.5 text-brand-600" />
            {currentSubject?.name || 'Subject'}
          </span>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-semibold">
            Class {currentSubject?.class || '9/10'}
          </span>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <span className="text-slate-700">
            Ch {currentChapter?.number}: {currentChapter?.title || 'Chapter'}
          </span>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <span className="text-brand-700 font-semibold truncate max-w-xs">
            {currentTopic?.title || 'Topic'}
          </span>
        </nav>

        {/* Title & Cache Status */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pt-1">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {outline.title || currentTopic?.title}
              </h2>
              {outlineMeta?.cached ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  <Database className="w-3 h-3 text-blue-600" />
                  Cached in Database
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-brand-700 border border-emerald-200">
                  <Sparkles className="w-3 h-3 text-brand-600" />
                  Freshly Generated
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 flex items-center gap-3">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-slate-400" />
                Lesson Duration: <strong className="text-slate-700">{totalMinutes} Minutes</strong>
              </span>
              {outlineMeta?.model && (
                <span className="hidden sm:inline text-xs text-slate-400">
                  • Model: {outlineMeta.model}
                </span>
              )}
            </p>
          </div>

          {/* Action Buttons: Copy & Regenerate */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-sm font-semibold transition active:scale-95 shadow-sm"
              title="Copy outline as text"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-emerald-600" />
                  <span className="text-emerald-700">Copied to Clipboard!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 text-slate-500" />
                  <span>Copy Outline</span>
                </>
              )}
            </button>

            <button
              onClick={() => generateOutline(true)}
              disabled={isGeneratingOutline}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-brand-200 bg-brand-50 hover:bg-brand-100 text-brand-700 text-sm font-semibold transition active:scale-95 disabled:opacity-50 shadow-sm"
              title="Regenerate with AI"
            >
              <RotateCw className={`w-4 h-4 text-brand-600 ${isGeneratingOutline ? 'animate-spin' : ''}`} />
              <span>{isGeneratingOutline ? 'Regenerating...' : 'Regenerate'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Main Outline Content Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card: Learning Objectives */}
        <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
          <div className="flex items-center gap-2.5 pb-4 mb-4 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Student Learning Outcomes (SLOs)</h3>
              <p className="text-xs text-slate-500">What students will know and be able to do</p>
            </div>
          </div>
          <ul className="space-y-3">
            {outline.learning_objectives?.map((objective, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-slate-700 leading-relaxed">
                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-brand-100 text-brand-800 text-xs font-bold shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span>{objective}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Card: Key Concepts & Definitions */}
        <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
          <div className="flex items-center gap-2.5 pb-4 mb-4 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Key Concepts & Terminology</h3>
              <p className="text-xs text-slate-500">Official definitions from the textbook excerpt</p>
            </div>
          </div>
          <div className="space-y-3">
            {outline.key_concepts?.map((concept, idx) => (
              <div key={idx} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                <span className="font-semibold text-slate-900 text-sm block mb-1">
                  {concept.term}
                </span>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  {concept.explanation}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* 3. Card: Lesson Flow Timeline */}
      <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">40–45 Min Period Breakdown</h3>
              <p className="text-xs text-slate-500">Step-by-step classroom instructional timeline</p>
            </div>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
            {totalMinutes} mins total
          </span>
        </div>

        <div className="relative pl-6 sm:pl-8 border-l-2 border-indigo-100 space-y-6 my-2">
          {outline.lesson_flow?.map((step, idx) => (
            <div key={idx} className="relative group">
              {/* Timeline marker */}
              <div className="absolute -left-[31px] sm:-left-[39px] top-0 flex items-center justify-center w-7 h-7 rounded-full bg-white border-2 border-indigo-500 text-indigo-700 text-xs font-bold shadow-sm">
                {idx + 1}
              </div>

              <div className="rounded-2xl bg-slate-50/70 p-4 sm:p-5 border border-slate-100 hover:border-slate-200 transition">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                  <h4 className="text-sm font-bold text-slate-900">{step.step}</h4>
                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md bg-indigo-100/70 text-indigo-800">
                    <Clock className="w-3 h-3" />
                    {step.duration_minutes} min
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  {step.details}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Activities & Check Questions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Classroom Activities */}
        <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
          <div className="flex items-center gap-2.5 pb-4 mb-4 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Low-Resource Classroom Activities</h3>
              <p className="text-xs text-slate-500">Board demonstrations and interactive peer tasks</p>
            </div>
          </div>
          <ul className="space-y-3">
            {outline.activities?.map((activity, idx) => (
              <li key={idx} className="flex items-start gap-3 p-3 rounded-2xl bg-purple-50/40 border border-purple-100/60 text-xs sm:text-sm text-slate-700 leading-relaxed">
                <span className="w-5 h-5 rounded-lg bg-purple-200/70 text-purple-900 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span>{activity}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Assessment / Check Questions */}
        <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
          <div className="flex items-center gap-2.5 pb-4 mb-4 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-sky-50 text-sky-600">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Formative Assessment Questions</h3>
              <p className="text-xs text-slate-500">Quick concept checks for the end of the period</p>
            </div>
          </div>
          <div className="space-y-3">
            {outline.check_questions?.map((question, idx) => (
              <div key={idx} className="p-3.5 rounded-2xl bg-sky-50/40 border border-sky-100/60 text-xs sm:text-sm text-slate-800 leading-relaxed flex items-start gap-2.5">
                <span className="font-bold text-sky-700 shrink-0">Q{idx + 1}:</span>
                <span>{question}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};
