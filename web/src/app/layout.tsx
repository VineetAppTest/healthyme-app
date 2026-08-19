import type { Metadata } from "next";

import { APP_DESCRIPTION, APP_NAME } from "@/lib/brand";

import "./globals.css";

export const metadata: Metadata = {
  title: `${APP_NAME} Web`,
  description: APP_DESCRIPTION,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
