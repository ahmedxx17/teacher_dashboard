import { create } from 'zustand';
import { supabase } from '../lib/supabaseClient';

export const useCurriculumStore = create((set, get) => ({
  // State
  subjects: [],
  chapters: [],
  topics: [],

  selectedSubject: '',
  selectedChapter: '',
  selectedTopic: '',

  outline: null,
  outlineMeta: null, // { cached: boolean, model: string, createdAt: string }

  isLoadingSubjects: false,
  isLoadingChapters: false,
  isLoadingTopics: false,
  isGeneratingOutline: false,
  error: null,

  // Actions
  loadSubjects: async () => {
    set({ isLoadingSubjects: true, error: null });
    try {
      const { data, error } = await supabase
        .from('subjects')
        .select('*')
        .order('class', { ascending: true })
        .order('name', { ascending: true });

      if (error) throw error;
      set({ subjects: data || [], isLoadingSubjects: false });
    } catch (err) {
      console.error('Failed to load subjects:', err);
      set({
        error: `Could not load subjects: ${err.message || 'Please check your Supabase connection'}`,
        isLoadingSubjects: false,
      });
    }
  },

  selectSubject: async (subjectId) => {
    if (!subjectId) {
      set({
        selectedSubject: '',
        selectedChapter: '',
        selectedTopic: '',
        chapters: [],
        topics: [],
        outline: null,
        outlineMeta: null,
      });
      return;
    }

    set({
      selectedSubject: subjectId,
      selectedChapter: '',
      selectedTopic: '',
      chapters: [],
      topics: [],
      outline: null,
      outlineMeta: null,
      isLoadingChapters: true,
      error: null,
    });

    try {
      const { data, error } = await supabase
        .from('chapters')
        .select('*')
        .eq('subject_id', subjectId)
        .order('number', { ascending: true });

      if (error) throw error;
      set({ chapters: data || [], isLoadingChapters: false });
    } catch (err) {
      console.error('Failed to load chapters:', err);
      set({
        error: `Could not load chapters: ${err.message}`,
        isLoadingChapters: false,
      });
    }
  },

  selectChapter: async (chapterId) => {
    if (!chapterId) {
      set({
        selectedChapter: '',
        selectedTopic: '',
        topics: [],
        outline: null,
        outlineMeta: null,
      });
      return;
    }

    set({
      selectedChapter: chapterId,
      selectedTopic: '',
      topics: [],
      outline: null,
      outlineMeta: null,
      isLoadingTopics: true,
      error: null,
    });

    try {
      const { data, error } = await supabase
        .from('topics')
        .select('id, title, order_index, start_page, end_page')
        .eq('chapter_id', chapterId)
        .order('order_index', { ascending: true });

      if (error) throw error;
      set({ topics: data || [], isLoadingTopics: false });
    } catch (err) {
      console.error('Failed to load topics:', err);
      set({
        error: `Could not load topics: ${err.message}`,
        isLoadingTopics: false,
      });
    }
  },

  selectTopic: async (topicId) => {
    if (!topicId) {
      set({ selectedTopic: '', outline: null, outlineMeta: null });
      return;
    }

    set({ selectedTopic: topicId, outline: null, outlineMeta: null, error: null });

    // Check if an outline is already cached for quick instant viewing
    try {
      const { data, error } = await supabase
        .from('outlines')
        .select('content, model, created_at')
        .eq('topic_id', topicId)
        .maybeSingle();

      if (!error && data) {
        set({
          outline: data.content,
          outlineMeta: {
            cached: true,
            model: data.model,
            createdAt: data.created_at,
          },
        });
      }
    } catch (err) {
      // Non-fatal cache prefetch error; teacher can still click generate
      console.warn('Cache prefetch error:', err);
    }
  },

  generateOutline: async (regenerate = false) => {
    const { selectedTopic } = get();
    if (!selectedTopic) return;

    set({ isGeneratingOutline: true, error: null });

    try {
      const { data, error } = await supabase.functions.invoke('generate-outline', {
        body: { topicId: selectedTopic, regenerate },
      });

      if (error) {
        throw new Error(error.message || 'Edge function execution failed');
      }

      if (data?.error) {
        throw new Error(data.error);
      }

      set({
        outline: data.outline,
        outlineMeta: {
          cached: Boolean(data.cached),
          model: data.model,
          createdAt: data.createdAt,
        },
        isGeneratingOutline: false,
      });
    } catch (err) {
      console.error('Generate outline failed:', err);
      set({
        error: `Failed to generate outline: ${err.message || 'Unknown error occurred'}`,
        isGeneratingOutline: false,
      });
    }
  },

  clearError: () => set({ error: null }),
}));
