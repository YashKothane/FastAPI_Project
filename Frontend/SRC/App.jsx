import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import BlogList from "./pages/BlogList";
import BlogDetail from "./pages/BlogDetail";
import BlogEditor from "./pages/BlogEditor";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<BlogList />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/blogs/new" element={<BlogEditor />} />
      <Route path="/blogs/:id" element={<BlogDetail />} />
      <Route path="/blogs/:id/edit" element={<BlogEditor />} />
    </Routes>
  );
}