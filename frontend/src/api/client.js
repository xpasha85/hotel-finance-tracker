import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
});

// временно: если хотим быть админом
export function setAdminMode(enabled) {
  if (enabled) {
    api.defaults.headers.common["X-Role"] = "ADMIN";
  } else {
    delete api.defaults.headers.common["X-Role"];
  }
}
