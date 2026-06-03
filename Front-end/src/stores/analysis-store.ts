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
  jobPosition?: string;
  employmentType?: string;
  notes?: string;
  suspiciousObservations?: string;
  documentSource?: string;
  payrollPeriod?: string;
  comments?: string;
}

interface AnalysisStore {
  // Upload state
  files: UploadedFile[];
  maxFiles: number;
  addFile: (file: UploadedFile) => void;
  updateFileProgress: (id: string, progress: number) => void;
  removeFile: (id: string) => void;
  clearFiles: () => void;

  // Extra info
  extraInfo: ExtraInfo;
  setExtraInfo: (info: Partial<ExtraInfo>) => void;
  clearExtraInfo: () => void;

  // Processing
  currentStage: AnalysisStage;
  stageProgress: number;
  isProcessing: boolean;
  setStage: (stage: AnalysisStage) => void;
  setStageProgress: (progress: number) => void;
  setIsProcessing: (v: boolean) => void;

  // Results
  results: AnalysisResult[];
  setResults: (results: AnalysisResult[]) => void;
  addResult: (result: AnalysisResult) => void;
  clearResults: () => void;

  // History
  history: HistoryEntry[];
  setHistory: (history: HistoryEntry[]) => void;
  addHistoryEntry: (entry: HistoryEntry) => void;
  removeHistoryEntry: (id: string) => void;

  // Reset
  resetAll: () => void;
}

const generateId = () => `doc-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

/* ═══════════════════════════════════════════════════
   Store
   ═══════════════════════════════════════════════════ */

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  // Upload
  files: [],
  maxFiles: 3,
  addFile: (file) =>
    set((s) => ({
      files: s.files.length < s.maxFiles ? [...s.files, file] : s.files,
    })),
  updateFileProgress: (id, progress) =>
    set((s) => ({
      files: s.files.map((f) => (f.id === id ? { ...f, progress, status: progress >= 100 ? "done" : "uploading" } : f)),
    })),
  removeFile: (id) => set((s) => ({ files: s.files.filter((f) => f.id !== id) })),
  clearFiles: () => set({ files: [] }),

  // Extra info
  extraInfo: {},
  setExtraInfo: (info) => set((s) => ({ extraInfo: { ...s.extraInfo, ...info } })),
  clearExtraInfo: () => set({ extraInfo: {} }),

  // Processing
  currentStage: "idle",
  stageProgress: 0,
  isProcessing: false,
  setStage: (stage) => set({ currentStage: stage }),
  setStageProgress: (progress) => set({ stageProgress: progress }),
  setIsProcessing: (v) => set({ isProcessing: v }),

  // Results
  results: [],
  setResults: (results) => set({ results }),
  addResult: (result) => set((s) => ({ results: [...s.results, result] })),
  clearResults: () => set({ results: [] }),

  // History
  history: [],
  setHistory: (history) => set({ history }),
  addHistoryEntry: (entry) =>
    set((s) => ({ history: [entry, ...s.history] })),
  removeHistoryEntry: (id) =>
    set((s) => ({ history: s.history.filter((h) => h.id !== id) })),

  // Reset
  resetAll: () =>
    set({
      files: [],
      extraInfo: {},
      currentStage: "idle",
      stageProgress: 0,
      isProcessing: false,
      results: [],
    }),
}));

export { generateId };
