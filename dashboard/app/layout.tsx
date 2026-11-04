import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Olist Commerce Pulse | E-commerce Analytics",
  description:
    "An end-to-end analytics project covering Olist commercial, customer, product, and delivery performance.",
  openGraph: {
    title: "Olist Commerce Pulse",
    description: "Sales, delivery timing and repeat purchases in the Olist public dataset.",
    images: [{ url: "/og.png", width: 1440, height: 900 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Olist Commerce Pulse",
    description: "Sales, delivery timing and repeat purchases in the Olist public dataset.",
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
