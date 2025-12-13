import { api } from "./client";

export function getExpenseHistory(expenseId) {
  return api.get(`/expenses/${expenseId}/history`);
}
