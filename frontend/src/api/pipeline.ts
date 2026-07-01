import { post } from "./client";
import type {
  ClinicalAssessmentClassifyOut,
  ExplainabilityGenerateOut,
  LongitudinalAnalyzeOut,
  NotesGenerateOut,
  ReviewOut,
  ReviewRequest,
  VisionAnalyzeOut,
} from "../types/api";

export const runVision = (assessmentId: string) =>
  post<VisionAnalyzeOut>("/vision/analyze", { assessment_id: assessmentId });

export const runLongitudinal = (assessmentId: string) =>
  post<LongitudinalAnalyzeOut>("/longitudinal/analyze", {
    assessment_id: assessmentId,
  });

export const runClassify = (assessmentId: string) =>
  post<ClinicalAssessmentClassifyOut>("/clinical-assessment/classify", {
    assessment_id: assessmentId,
  });

export const runExplainability = (assessmentId: string) =>
  post<ExplainabilityGenerateOut>("/explainability/generate", {
    assessment_id: assessmentId,
  });

export const submitReview = (payload: ReviewRequest) =>
  post<ReviewOut>("/review", payload);

export const generateNote = (assessmentId: string) =>
  post<NotesGenerateOut>("/notes/generate", { assessment_id: assessmentId });
