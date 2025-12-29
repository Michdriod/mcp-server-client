import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import QueryPage from "./pages/QueryPage";
import SavedQueriesPage from "./pages/SavedQueriesPage";
import HistoryPage from "./pages/HistoryPage";
import DashboardPage from "./pages/DashboardPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SchemaExplorerPage from "./pages/SchemaExplorerPage";
import ScheduledReportsPage from "./pages/ScheduledReportsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<ProtectedRoute><QueryPage /></ProtectedRoute>} />
            <Route path="/saved" element={<ProtectedRoute><SavedQueriesPage /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute requiredRole="analyst"><AnalyticsPage /></ProtectedRoute>} />
            <Route path="/schema" element={<ProtectedRoute><SchemaExplorerPage /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute requiredRole="analyst"><ScheduledReportsPage /></ProtectedRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
