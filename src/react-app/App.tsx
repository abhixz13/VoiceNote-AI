import { BrowserRouter as Router, Routes, Route } from "react-router";
import HomePage from "@/react-app/pages/Home";
import RecordPage from "@/react-app/pages/Record";
import RecordingsPage from "@/react-app/pages/Recordings";
import RecordingDetailPage from "@/react-app/pages/RecordingDetail";

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
