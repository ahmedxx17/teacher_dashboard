import React from 'react';
import { useCurriculumStore } from '../store/useCurriculumStore';
import { CheckSquare, Square, Check, X, Layers, Loader2, AlertCircle } from 'lucide-react';

export const TopicSelect = () => {
  const {
    topics,
    selectedChapter,
    selectedTopicIds,
    toggleTopic,
    selectAllTopics,
    clearTopics,
    isLoadingTopics,
    numLessons,
  } = useCurriculumStore();

  const isAllSelected = topics.length > 0 && selectedTopicIds.length === topics.length;

  if (!selectedChapter) {
    return (
      <div className="flex flex-col gap-2 w-full">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
          <Layers className="w-4 h-4 text-slate-400" />
          <span>3. Select Topics</span>
        </label>
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 p-5 text-center text-xs text-slate-400">
          First select a chapter above to see and select topics
        </div>
      </div>
    );
  }

  if (isLoadingTopics) {
    return (
      <div className="flex flex-col gap-2 w-full">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
          <Layers className="w-4 h-4 text-brand-600" />
          <span>3. Select Topics</span>
        </label>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 flex items-center justify-center gap-2.5 text-xs text-slate-500 shadow-sm">
          <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
          <span>Loading topics from chapter...</span>
        </div>
      </div>
    );
  }

  if (topics.length === 0) {
    return (
      <div className="flex flex-col gap-2 w-full">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
          <Layers className="w-4 h-4 text-brand-600" />
          <span>3. Select Topics</span>
        </label>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 text-center text-xs text-slate-400 shadow-sm">
          No topics found for this chapter in textbook.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 w-full">
      {/* Header bar with Select All / Clear */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-brand-600" />
            <span>3. Select Topics</span>
          </label>
          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-brand-50 text-brand-800 border border-brand-200">
            {selectedTopicIds.length} of {topics.length} selected
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={selectAllTopics}
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition ${
              isAllSelected
                ? 'bg-slate-100 text-slate-400 cursor-default'
                : 'bg-brand-50 hover:bg-brand-100 text-brand-700'
            }`}
            disabled={isAllSelected}
          >
            <Check className="w-3.5 h-3.5" />
            <span>Select all</span>
          </button>

          <button
            type="button"
            onClick={clearTopics}
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg font-medium transition ${
              selectedTopicIds.length === 0
                ? 'bg-slate-100 text-slate-400 cursor-default'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
            }`}
            disabled={selectedTopicIds.length === 0}
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Checkbox list container */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-2.5 max-h-64 sm:max-h-72 overflow-y-auto space-y-1.5 shadow-inner">
        {topics.map((top) => {
          const isSelected = selectedTopicIds.includes(top.id);
          return (
            <label
              key={top.id}
              onClick={() => toggleTopic(top.id)}
              className={`flex items-start gap-3 p-3 rounded-xl border text-xs sm:text-sm font-medium transition cursor-pointer select-none ${
                isSelected
                  ? 'bg-white border-brand-300 shadow-sm text-slate-900 ring-1 ring-brand-500/20'
                  : 'bg-white/80 border-slate-200/90 text-slate-700 hover:border-slate-300 hover:bg-white'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                <div
                  className={`w-4 h-4 rounded-md border flex items-center justify-center transition ${
                    isSelected
                      ? 'bg-brand-600 border-brand-600 text-white'
                      : 'border-slate-300 bg-white'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
              </div>

              <div className="flex-1 min-w-0">
                <span className="leading-snug block font-medium">
                  {top.title}
                </span>
              </div>

              {top.start_page && (
                <span className="text-[11px] font-normal text-slate-400 shrink-0 px-2 py-0.5 rounded bg-slate-100">
                  pp. {top.start_page}–{top.end_page || top.start_page}
                </span>
              )}
            </label>
          );
        })}
      </div>

      {/* Bottom Hint */}
      {selectedTopicIds.length === 0 ? (
        <div className="flex items-center gap-1.5 text-xs text-amber-600 font-medium pt-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>At least one topic must be selected to generate an outline.</span>
        </div>
      ) : (
        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-0.5 px-1">
          <span>
            {selectedTopicIds.length === 1
              ? '1 topic selected'
              : `${selectedTopicIds.length} topics selected in book order`}
          </span>
          <span className="text-slate-400">
            {selectedTopicIds.length === numLessons
              ? `Mapped ~1 topic per lesson (${numLessons} lessons)`
              : `Paced across ${numLessons} lesson(s)`}
          </span>
        </div>
      )}
    </div>
  );
};
