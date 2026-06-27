import React from "react";
import ReactDOM from "react-dom/client";
import { DashboardPage } from "./pages/DashboardPage";
import { LogsViewPage } from "./pages/LogsViewPage";
import "./styles.css";

function App() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("view") === "logs") {
    return <LogsViewPage />;
  }
  return <DashboardPage />;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
