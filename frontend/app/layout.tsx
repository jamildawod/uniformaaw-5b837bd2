import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "Uniforma",
  description: "Uniforma storefront",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="sv">
      <body>{children}</body>
    </html>
  );
}
