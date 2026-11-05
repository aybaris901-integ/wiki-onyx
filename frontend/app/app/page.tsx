import type { Metadata } from "next";
import { Ask } from "./ask";
import "./app.css";

export const metadata: Metadata = { title: "Ask the brain | Company Brain" };

export default function AppPage() {
  return <Ask />;
}
