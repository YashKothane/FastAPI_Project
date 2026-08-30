import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBlogs } from "../api/blogs";
// import { useAuth } from "../context/AuthContext"; // only if you built AuthContext for this project too

export default function BlogList() {
  const [blogs, setBlogs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBlogs()
      .then(setBlogs)
      .catch(() => setError("Couldn't load blogs."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading…</p>;

  return (
    <div style={{ maxWidth: 700, margin: "40px auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Blogs</h1>
        <Link to="/blogs/new">Write a post</Link>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {blogs.map((blog) => (
        <div key={blog.id} style={{ borderBottom: "1px solid #ddd", padding: "16px 0" }}>
          <h2 style={{ marginBottom: 4 }}>
            <Link to={`/blogs/${blog.id}`}>{blog.title}</Link>
          </h2>
          <p style={{ color: "#666", fontSize: 14 }}>
            By {blog.author_name} · {new Date(blog.created_at).toLocaleDateString()}
          </p>
          <p>{blog.content.slice(0, 160)}{blog.content.length > 160 ? "…" : ""}</p>
        </div>
      ))}

      {blogs.length === 0 && <p>No blogs yet. Be the first to write one!</p>}
    </div>
  );
}