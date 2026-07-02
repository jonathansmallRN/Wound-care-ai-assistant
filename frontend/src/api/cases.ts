import { get, post } from "./client";
import type { CaseDetailOut, CaseListItemOut, CaseOut } from "../types/api";

export const listCases = () => get<CaseListItemOut[]>("/cases");

export const getCase = (id: string) => get<CaseDetailOut>(`/cases/${id}`);

export const createCase = (caseRef: string) =>
  post<CaseOut>("/cases", { case_ref: caseRef });
