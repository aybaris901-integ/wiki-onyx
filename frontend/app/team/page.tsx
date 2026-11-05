import type { Metadata } from "next";
import { Team } from "./team";
import "../app/app.css";
import "./team.css";

export const metadata: Metadata = { title: "Team | Company Brain" };

export default function TeamPage() {
  return <Team />;
}
