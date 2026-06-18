import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'YOLO Pose 자세 분석기' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
