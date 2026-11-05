import type { Metadata } from "next";
import { Mona_Sans } from "next/font/google";
import "./globals.css";

const mona = Mona_Sans({ subsets: ["latin"], axes: ["wdth"], variable: "--font-mona" });

export const metadata: Metadata = {
  title: "Company Brain",
  description:
    "Ask why anything at your company is built the way it is. Get who wrote it, why, where it was discussed and who owns it now.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={mona.variable}>
      <body>{children}</body>
    </html>
  );
}
