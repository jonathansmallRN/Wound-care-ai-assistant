import { get, post } from "./client";
import type {
  AssessmentCreate,
  AssessmentCreateOut,
  AssessmentDetailOut,
} from "../types/api";

export const createAssessment = (payload: AssessmentCreate) =>
  post<AssessmentCreateOut>("/assessments", payload);

export const getAssessment = (id: string) =>
  get<AssessmentDetailOut>(`/assessments/${id}`);

export const listAssessmentsForCase = (caseId: string) =>
  get<AssessmentDetailOut[]>(`/cases/${caseId}/assessments`);
