// src/frontend/src/app/layout.tsx
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: 'swap', // Add display swap for better font loading
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: 'swap',
})

export const metadata: Metadata = {
  title: "Sergek Road Incident Detection",
  description: "Video processing application for road incident detection",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body
        className="antialiased"
        suppressHydrationWarning={true}
      >
        {children}
      </body>
    </html>
  )
}
