import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 고객센터",
  description: "CrewAI 멀티에이전트 고객센터",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" style={{ height: '100%', overflow: 'hidden' }}>
      <body style={{ height: '100%', overflow: 'hidden', margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
