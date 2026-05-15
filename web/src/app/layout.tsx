import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "tools-project",
  description: "Internal project management hub",
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
