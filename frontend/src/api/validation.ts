import { get } from "./client";
import type {
  ValidationBySkinToneOut,
  ValidationByReviewerOut,
  ValidationSummaryOut,
} from "../types/api";

export const getValidationSummary = () =>
  get<ValidationSummaryOut>("/validation/summary");

export const getValidationByReviewer = () =>
  get<ValidationByReviewerOut[]>("/validation/by-reviewer");

export const getValidationBySkinTone = () =>
  get<ValidationBySkinToneOut[]>("/validation/by-skin-tone");
