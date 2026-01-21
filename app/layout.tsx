import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lexicon-AI | AI-Powered Legal Research Platform",
  description:
    "Professional legal research platform powered by AI. Search case law, statutes, regulations, and legal articles with advanced AI assistance.",
  keywords: [
    "legal research",
    "AI legal assistant",
    "case law",
    "legal database",
    "legal AI",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
