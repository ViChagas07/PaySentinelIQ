"use client";

import { create } from "zustand";

/* ═══════════════════════════════════════════════════
   Types
   ═══════════════════════════════════════════════════ */

export type AnalysisType = "payroll" | "bank-slip";

export type AnalysisStage =
  | "idle"
  | "uploading"
  | "ocr"
  | "metadata"
  | "fraud-detection"
  | "financial-check"
  | "risk-analysis"
  | "report-generation"
  | "complete";

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: "pending" | "uploading" | "done" | "error";
  preview?: string;
  /** The actual File object — needed for multipart upload to analysis endpoint. */
  file?: File;
}

export interface AnalysisResult {
  id: string;
  fileName: string;
  documentType: AnalysisType;
  riskScore: number;
  fraudProbability: number;
  confidenceScore: number;
  aiSummary: string;
  ocrData: Record<string, string>;
  metadata: Record<string, string>;
  financialInconsistencies: string[];
  manipulationIndicators: string[];
  recommendedActions: string[];
  analysisTimeline: { stage: string; duration: number; status: "pass" | "warn" | "fail" }[];
  statusIndicators: { label: string; value: boolean; severity: "low" | "medium" | "high" | "critical" }[];
  createdAt: string;
  processingDuration: number;
}

export interface HistoryEntry {
  id: string;
  fileName: string;
  documentType: AnalysisType;
  uploadDate: string;
  status: "completed" | "flagged" | "failed";
  riskScore: number;
  processingDuration: number;
  aiSummary: string;
  resultId: string;
}

export interface ExtraInfo {
  employeeName?: string;
  companyName?: string;
  expectedSalary?: string;
  expectedAmount?: string;
  recipientName?: string;
  jobPosition?: string;
  employmentType?: string;
  notes?: string;
  suspiciousObservations?: string;
  documentSource?: string;
  payrollPeriod?: string;
  comments?: string;
}

/** Per-analysis-type state */
interface AnalysisTypeState {
  files: UploadedFile[];
  extraInfo: ExtraInfo;
  currentStage: AnalysisStage;
  stageProgress: number;
  isProcessing: boolean;
  results: AnalysisResult[];
  history: HistoryEntry[];
}

interface AnalysisStore {
  // Per-type state
  states: Record<AnalysisType, AnalysisTypeState>;
  maxFiles: number;

  // Actions with analysis type parameter
  addFile: (type: AnalysisType, file: UploadedFile) => void;
  updateFileProgress: (type: AnalysisType, id: string, progress: number) => void;
  removeFile: (type: AnalysisType, id: string) => void;
  clearFiles: (type: AnalysisType) => void;

  setExtraInfo: (type: AnalysisType, info: Partial<ExtraInfo>) => void;
  clearExtraInfo: (type: AnalysisType) => void;
  getExtraInfo: (type: AnalysisType) => ExtraInfo;

  setStage: (type: AnalysisType, stage: AnalysisStage) => void;
  setStageProgress: (type: AnalysisType, progress: number) => void;
  setIsProcessing: (type: AnalysisType, v: boolean) => void;

  setResults: (type: AnalysisType, results: AnalysisResult[]) => void;
  addResult: (type: AnalysisType, result: AnalysisResult) => void;
  clearResults: (type: AnalysisType) => void;

  setHistory: (type: AnalysisType, history: HistoryEntry[]) => void;
  addHistoryEntry: (type: AnalysisType, entry: HistoryEntry) => void;
  removeHistoryEntry: (type: AnalysisType, id: string) => void;

  resetAll: (type: AnalysisType) => void;
  resetAllTypes: () => void;
}

const generateId = () => `doc-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

const createInitialTypeState = (): AnalysisTypeState => ({
  files: [],
  extraInfo: {},
  currentStage: "idle",
  stageProgress: 0,
  isProcessing: false,
  results: [],
  history: [],
});

/* ═══════════════════════════════════════════════════
   Store
   ═══════════════════════════════════════════════════ */

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  // Upload
  maxFiles: 3,
  states: {
    payroll: createInitialTypeState(),
    "bank-slip": createInitialTypeState(),
  },

  addFile: (type, file) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: {
          ...s.states[type],
          files: s.states[type].files.length < s.maxFiles ? [...s.states[type].files, file] : s.states[type].files,
        },
      },
    })),

  updateFileProgress: (type, id, progress) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: {
          ...s.states[type],
          files: s.states[type].files.map((f) =>
            f.id === id ? { ...f, progress, status: progress >= 100 ? "done" : "uploading" } : f
          ),
        },
      },
    })),

  removeFile: (type, id) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: {
          ...s.states[type],
          files: s.states[type].files.filter((f) => f.id !== id),
        },
      },
    })),

  clearFiles: (type) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], files: [] },
      },
    })),

  // Extra info
  setExtraInfo: (type, info) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: {
          ...s.states[type],
          extraInfo: { ...s.states[type].extraInfo, ...info },
        },
      },
    })),
  clearExtraInfo: (type) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], extraInfo: {} },
      },
    })),
  getExtraInfo: (type) => {
    // This is a getter, not an action - we'll use selector pattern instead
    return {} as ExtraInfo; // Placeholder, actual value comes from selector
  },

  // Processing
  setStage: (type, stage) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], currentStage: stage },
      },
    })),
  setStageProgress: (type, progress) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], stageProgress: progress },
      },
    })),
  setIsProcessing: (type, v) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], isProcessing: v },
      },
    })),

  // Results
  setResults: (type, results) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], results },
      },
    })),
  addResult: (type, result) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], results: [...s.states[type].results, result] },
      },
    })),
  clearResults: (type) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], results: [] },
      },
    })),

  // History
  setHistory: (type, history) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], history },
      },
    })),
  addHistoryEntry: (type, entry) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], history: [entry, ...s.states[type].history] },
      },
    })),
  removeHistoryEntry: (type, id) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: { ...s.states[type], history: s.states[type].history.filter((h) => h.id !== id) },
      },
    })),

  // Reset
  resetAll: (type) =>
    set((s) => ({
      states: {
        ...s.states,
        [type]: createInitialTypeState(),
      },
    })),
  resetAllTypes: () =>
    set({
      states: {
        payroll: createInitialTypeState(),
        "bank-slip": createInitialTypeState(),
      },
    }),
}));

/** Selector helpers for per-type state */
export const selectFiles = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].files;
export const selectExtraInfo = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].extraInfo;
export const selectCurrentStage = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].currentStage;
export const selectStageProgress = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].stageProgress;
export const selectIsProcessing = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].isProcessing;
export const selectResults = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].results;
export const selectHistory = (type: AnalysisType) => (state: AnalysisStore) => state.states[type].history;
export const selectMaxFiles = (state: AnalysisStore) => state.maxFiles;
export const selectAddFile = (state: AnalysisStore) => state.addFile;
export const selectRemoveFile = (state: AnalysisStore) => state.removeFile;
export const selectUpdateFileProgress = (state: AnalysisStore) => state.updateFileProgress;
export const selectSetExtraInfo = (state: AnalysisStore) => state.setExtraInfo;
export const selectClearExtraInfo = (state: AnalysisStore) => state.clearExtraInfo;
export const selectClearFiles = (state: AnalysisStore) => state.clearFiles;
export const selectClearResults = (state: AnalysisStore) => state.clearResults;
export const selectAddResult = (state: AnalysisStore) => state.addResult;
export const selectAddHistoryEntry = (state: AnalysisStore) => state.addHistoryEntry;
export const selectRemoveHistoryEntry = (state: AnalysisStore) => state.removeHistoryEntry;
export const selectResetAll = (state: AnalysisStore) => state.resetAll;

/** Combined selectors across all types */
export const selectAllResults = (state: AnalysisStore) => [...state.states.payroll.results, ...state.states["bank-slip"].results];
export const selectAnyIsProcessing = (state: AnalysisStore) => state.states.payroll.isProcessing || state.states["bank-slip"].isProcessing;
export const selectLatestStage = (state: AnalysisStore) => state.states.payroll.currentStage !== "idle" ? state.states.payroll.currentStage : state.states["bank-slip"].currentStage;

export { generateId };
