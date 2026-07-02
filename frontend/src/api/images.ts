import { postForm } from "./client";

export interface ImageUploadOut {
  image_id: string;
  storage_url: string;
  filename: string;
}

export const uploadImage = (assessmentId: string, file: File) => {
  const form = new FormData();
  form.append("assessment_id", assessmentId);
  form.append("image_file", file);
  return postForm<ImageUploadOut>("/images", form);
};
