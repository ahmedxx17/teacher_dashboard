import React, { useState } from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import {
  BookOpen,
  Calendar,
  Trash2,
  ExternalLink,
  RotateCw,
  Loader2,
  Sparkles,
} from 'lucide-react';

export const SavedOutlinesPanel = () => {
  const {
    savedOutlines,
    isLoadingSavedOutlines,
    deleteSavedOutline,
    viewSavedOutline,
    regenerateWithSettings,
    setActiveView,
  } = useCurriculumStore();

  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                My Saved Outlines
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-50 text-brand-800 border border-brand-200">
                {savedOutlines.length} {savedOutlines.length === 1 ? 'Plan' : 'Plans'}
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              Access, print, and reuse your curriculum lesson plans anytime on this device.
            </p>
          </div>

          <button
            onClick={() => setActiveView('generator')}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs sm:text-sm font-semibold transition active:scale-95 shadow-sm shadow-brand-600/20 shrink-0 self-start sm:self-auto"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate New Outline</span>
          </button>
        </div>
      </div>

      {/* 2. Saved Outlines List */}
      {isLoadingSavedOutlines ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center text-xs text-slate-500 shadow-sm flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
          <span>Loading your saved outlines...</span>
        </div>
      ) : savedOutlines.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-12 sm:p-16 text-center shadow-xs">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 mb-4">
            <BookOpen className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-800 mb-1">
            No Saved Outlines Yet
          </h3>
          <p className="text-xs sm:text-sm text-slate-500 max-w-sm mx-auto mb-6">
            Generate any lesson plan in the outline generator and click the <strong>"Save"</strong> button to store it here for future classes.
          </p>
          <button
            onClick={() => setActiveView('generator')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs sm:text-sm font-semibold transition active:scale-95 shadow-sm"
          >
            <Sparkles className="w-4 h-4" />
            <span>Go to Generator</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {savedOutlines.map((item) => {
            const isConfirming = confirmDeleteId === item.id;
            const formattedDate = new Date(item.created_at).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            });
            const settings = item.settings || {};
            const topicTitles = item.content?._meta?.topicTitles || [];

            return (
              <div
                key={item.id}
                className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs hover:border-slate-300 transition space-y-4"
              >
                {/* Header row: Subject, Class, Date, Chapter Title */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-brand-50 text-brand-800 border border-brand-200">
                        {item.subject} • Class {item.class}
                      </span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formattedDate}
                      </span>
                    </div>

                    <h3 className="text-base sm:text-lg font-bold text-slate-900 pt-0.5">
                      {item.content?.title || item.chapter_title}
                    </h3>

                    <p className="text-xs text-slate-500">
                      {item.chapter_title}
                    </p>
                  </div>

                  {/* Settings Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 self-start">
                    {settings.periodLength && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium border border-slate-200">
                        ⏱️ {settings.periodLength}m
                      </span>
                    )}
                    {settings.numLessons && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium border border-slate-200">
                        📚 {settings.numLessons} {settings.numLessons === 1 ? 'lesson' : 'lessons'}
                      </span>
                    )}
                    {settings.studentLevel && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium border border-slate-200">
                        🎯 {settings.studentLevel}
                      </span>
                    )}
                    {settings.outputLanguage && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium border border-slate-200">
                        🌐 {settings.outputLanguage}
                      </span>
                    )}
                  </div>
                </div>

                {/* Topics Covered */}
                {topicTitles.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 flex flex-wrap items-center gap-1.5">
                    <span className="font-semibold text-slate-500">Topics ({topicTitles.length}):</span>
                    {topicTitles.map((title, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px]">
                        {title}
                      </span>
                    ))}
                  </div>
                )}

                {/* Action Buttons Row */}
                <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {/* View Outline Button */}
                    <button
                      onClick={() => viewSavedOutline(item)}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold transition active:scale-95 shadow-sm"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>View & Print</span>
                    </button>

                    {/* Regenerate With Settings */}
                    <button
                      onClick={() => regenerateWithSettings(item)}
                      className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition active:scale-95 shadow-xs"
                      title="Load settings into generator"
                    >
                      <RotateCw className="w-3.5 h-3.5 text-slate-500" />
                      <span>Use These Settings</span>
                    </button>
                  </div>

                  {/* Delete with Confirmation Step */}
                  <div>
                    {isConfirming ? (
                      <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 px-2.5 py-1.5 rounded-xl">
                        <span className="text-xs text-rose-800 font-bold">Delete?</span>
                        <button
                          onClick={() => {
                            deleteSavedOutline(item.id);
                            setConfirmDeleteId(null);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-rose-600 text-white text-[11px] font-bold hover:bg-rose-700 transition"
                        >
                          Confirm
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="px-2 py-1 rounded-lg bg-slate-200 text-slate-700 text-[11px] font-medium hover:bg-slate-300 transition"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteId(item.id)}
                        className="inline-flex items-center gap-1 px-3 py-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 text-xs font-semibold transition"
                        title="Delete saved outline"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Delete</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
