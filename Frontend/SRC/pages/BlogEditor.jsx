import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createBlog, updateBlog, fetchBlog } from "../api/blogs";

export default function BlogEditor() {
  const { id } = useParams(); // undefined when creating a new post
  const isEditing = Boolean(id);
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isEditing) {
      fetchBlog(id).then((blog) => {
        setTitle(blog.title);
        setContent(blog.content);
      });
    }
  }, [id, isEditing]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const blog = isEditing
        ? await updateBlog(id, { title, content })
        : await createBlog({ title, content });
      navigate(`/blogs/${blog.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Couldn't save the post.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: "40px auto" }}>
      <h1>{isEditing ? "Edit post" : "Write a new post"}</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <input
            placeholder="Title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{ width: "100%", fontSize: 22, padding: 8, marginBottom: 12 }}
          />
        </div>
        <div>
          <textarea
            placeholder="Write your post..."
            required
            rows={16}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            style={{ width: "100%", fontSize: 16, padding: 8 }}
          />
        </div>
        <button type="submit" disabled={submitting} style={{ marginTop: 16 }}>
          {submitting ? "Saving…" : isEditing ? "Save changes" : "Publish"}
        </button>
      </form>
    </div>
  );
}