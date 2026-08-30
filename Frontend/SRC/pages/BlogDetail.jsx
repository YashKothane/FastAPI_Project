import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { fetchBlog, deleteBlog } from "../api/blogs";


export default function BlogDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [blog, setBlog] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchBlog(id)
      .then(setBlog)
      .catch(() => setError("Blog not found."));
  }, [id]);

  async function handleDelete() {
    if (!confirm("Delete this post? This can't be undone.")) return;
    try {
      await deleteBlog(id);
      navigate("/");
    } catch {
      alert("Couldn't delete — you may not own this post.");
    }
  }

  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!blog) return <p>Loading…</p>;

  return (
    <div style={{ maxWidth: 700, margin: "40px auto" }}>
      <Link to="/">← Back</Link>
      <h1>{blog.title}</h1>
      <p style={{ color: "#666", fontSize: 14 }}>
        By {blog.author_name} · {new Date(blog.created_at).toLocaleDateString()}
      </p>
      <div style={{ whiteSpace: "pre-wrap", marginTop: 20 }}>{blog.content}</div>

      <div style={{ marginTop: 30, display: "flex", gap: 12 }}>
        <Link to={`/blogs/${id}/edit`}>Edit</Link>
        <button onClick={handleDelete}>Delete</button>
      </div>
    </div>
  );
}
