import { api } from "./client";

export function uploadReceipt(expenseId, file) {
  const fd = new FormData();
  fd.append("file", file);
  return api.post(`/expenses/${expenseId}/receipt`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}
