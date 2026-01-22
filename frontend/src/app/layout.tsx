import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Lexicon AI - Legal Research Platform',
  description: 'AI-powered legal research and document intelligence platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
