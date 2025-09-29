import React from "react";
import { createRoot } from "react-dom/client";
import PickIQApp from "./PickIQApp.tsx";
import { ThemeProvider } from "./components/theme-provider";
import "./index.css";
import "./styles/mobile.css";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Failed to find the root element");

createRoot(rootElement).render(
  <React.StrictMode>
    <ThemeProvider>
      <PickIQApp />
    </ThemeProvider>
  </React.StrictMode>
);