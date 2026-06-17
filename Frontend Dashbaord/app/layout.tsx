import type React from "react"
import type { Metadata } from "next"
import { Bricolage_Grotesque } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "@/components/theme-provider"
import "./globals.css"

const bricolage = Bricolage_Grotesque({ subsets: ["latin"], display: "swap" })

export const metadata: Metadata = {
  title: "Oybit Command Center",
  description: "Manage all 7 social media bots from one central dashboard",
  generator: "v0.app",
  icons: {
    icon: [
      {
        url: "/icon-light-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/icon-dark-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/icon.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/apple-icon.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${bricolage.className} antialiased`}>
        <ThemeProvider defaultTheme="light" storageKey="oybit-theme">
          {children}
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
