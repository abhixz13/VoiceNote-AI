import { BrowserRouter as Router, Routes, Route } from "react-router";
import HomePage from "@/pages/Home";
import RecordPage from "@/pages/Record";
import RecordingsPage from "@/pages/Recordings";
import RecordingDetailPage from "@/pages/RecordingDetail";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/record" element={<RecordPage />} />
        <Route path="/recordings" element={<RecordingsPage />} />
        <Route path="/recordings/:id" element={<RecordingDetailPage />} />
      </Routes>
    </Router>
  );
}
