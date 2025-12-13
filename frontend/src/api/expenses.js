import { api } from "./client";

export function listExpenses(params) {
  return api.get("/expenses", { params });
}

export function createExpense(data) {
  return api.post("/expenses", data);
}

export function deleteExpense(id) {
  return api.post(`/expenses/${id}/delete`);
}

export function restoreExpense(id) {
  return api.post(`/expenses/${id}/restore`);
}

export function updateExpense(id, data) {
  return api.patch(`/expenses/${id}`, data);
}
