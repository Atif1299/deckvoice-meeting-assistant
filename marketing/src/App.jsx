import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Layout from "./Layout.jsx";
import HomePage from "./pages/HomePage.jsx";
import FeaturesPage from "./pages/FeaturesPage.jsx";
import PricingPage from "./pages/PricingPage.jsx";
import HowItWorksPage from "./pages/HowItWorksPage.jsx";
import UseCasesPage from "./pages/UseCasesPage.jsx";
import PrivacyPage from "./pages/PrivacyPage.jsx";
import TermsPage from "./pages/TermsPage.jsx";
import RefundPage from "./pages/RefundPage.jsx";
import ContactPage from "./pages/ContactPage.jsx";
import { trackPageView } from "./lib/analytics.js";

export default function App() {
  const location = useLocation();
  useEffect(() => {
    trackPageView(location.pathname);
  }, [location.pathname]);

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/use-cases" element={<UseCasesPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/refund" element={<RefundPage />} />
        <Route path="/contact" element={<ContactPage />} />
      </Route>
    </Routes>
  );
}
