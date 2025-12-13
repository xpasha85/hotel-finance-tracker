import { api } from "./client";

export function listCategories(params) {
  return api.get("/categories", { params });
}
