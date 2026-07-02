import { get } from "./client";
import type { AuditLogOut } from "../types/api";

export const getAuditLog = (assessmentId: string) =>
  get<AuditLogOut[]>(`/audit/${assessmentId}`);
