import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: "InterviewHub - AI Interview Preparation Assistant",
  description: "Get ready for your next interview with AI-powered personalized preparation checklists",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Sidebar />
        {children}
      </body>
    </html>
  );
}
