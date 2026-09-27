import React from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/AppLayout";
import ChatPage from "./pages/ChatPage";
import ConnectPage from "./pages/ConnectPage";
import PriorityChooser from "./components/PriorityChooser";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <HashRouter>
        <AppLayout appName={"LLM Bridge 範例"}>
          <Routes>
            {/* 第一次使用一定要先選優先順序:model="auto" 在使用者選之前會被 Bridge 拒絕 */}
            <Route path="/" element={<PriorityChooser gate><ChatPage /></PriorityChooser>} />
            <Route path="/connect" element={<ConnectPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AppLayout>
      </HashRouter>
    </>
  );
}
