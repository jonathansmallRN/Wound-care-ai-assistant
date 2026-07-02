import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CasesPage from "./pages/CasesPage";
import NewCasePage from "./pages/NewCasePage";
import CaseDetailPage from "./pages/CaseDetailPage";
import NewAssessmentPage from "./pages/NewAssessmentPage";
import AssessmentWorkflowPage from "./pages/AssessmentWorkflowPage";
import ValidationDashboardPage from "./pages/ValidationDashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<CasesPage />} />
          <Route path="cases/new" element={<NewCasePage />} />
          <Route path="cases/:caseId" element={<CaseDetailPage />} />
          <Route
            path="cases/:caseId/assessments/new"
            element={<NewAssessmentPage />}
          />
          <Route
            path="assessments/:assessmentId"
            element={<AssessmentWorkflowPage />}
          />
          <Route path="validation" element={<ValidationDashboardPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
