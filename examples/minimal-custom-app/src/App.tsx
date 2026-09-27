import React from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/AppLayout";
import ChatPage from "./pages/ChatPage";
import ConnectPage from "./pages/ConnectPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <HashRouter>
        <AppLayout appName={"LLM Bridge 範例"}>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/connect" element={<ConnectPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AppLayout>
      </HashRouter>
    </>
  );
}
