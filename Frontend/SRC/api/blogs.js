import { apiClient } from "./client";

export async function fetchBlogs() {
  const { data } = await apiClient.get("/blogs");
  return data;
}

export async function fetchBlog(id) {
  const { data } = await apiClient.get(`/blogs/${id}`);
  return data;
}

export async function createBlog({ title, content }) {
  const { data } = await apiClient.post("/blogs", { title, content });
  return data;
}

export async function updateBlog(id, { title, content }) {
  const { data } = await apiClient.put(`/blogs/${id}`, { title, content });
  return data;
}

export async function deleteBlog(id) {
  await apiClient.delete(`/blogs/${id}`);
}