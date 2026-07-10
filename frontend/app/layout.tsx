import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CropDoc",
  description: "Crop disease detection with an AI advisor chatbot",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
