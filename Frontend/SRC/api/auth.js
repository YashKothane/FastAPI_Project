import { apiClient } from "./client";

export async function signupUser({ name, email, password }) {
  const { data } = await apiClient.post("/signup", { name, email, password });
  return data;
}

export async function loginUser({ email, password }) {
  // FastAPI's OAuth2PasswordRequestForm expects form-encoded data,
  // with fields named "username" and "password" — not JSON.
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const { data } = await apiClient.post("/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}