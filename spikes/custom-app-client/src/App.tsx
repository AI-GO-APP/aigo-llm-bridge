import React from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/AppLayout";
import SpikePage from "./pages/SpikePage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <HashRouter>
        <AppLayout appName={"LLM Bridge Spike Client"}>
          <Routes>
            <Route path="/" element={<SpikePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AppLayout>
      </HashRouter>
    </>
  );
}
