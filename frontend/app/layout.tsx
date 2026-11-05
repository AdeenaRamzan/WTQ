import type { Metadata } from 'next'
import React from 'react'

export const metadata: Metadata = {
  metadataBase: new URL('https://utility-bill-decoder.vercel.app'),
  title: 'Utility Bill Decoder - Electricity Bill Intelligence & Results Viewer',
  description:
    'Front-end results viewer for Pakistani electricity bills (K-Electric, LESCO, IESCO). Instant visual breakdown of charges, taxes, meter readings, and AI question answers.',
  openGraph: {
    title: 'Utility Bill Decoder - Electricity Bill Intelligence & Results Viewer',
    description:
      'Front-end results viewer for Pakistani electricity bills (K-Electric, LESCO, IESCO). Instant visual breakdown of charges, taxes, meter readings, and AI question answers.',
    url: 'https://utility-bill-decoder.vercel.app',
    siteName: 'Utility Bill Decoder',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Utility Bill Decoder dashboard preview showing bill analysis, amount due, and verification breakdown',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Utility Bill Decoder - Electricity Bill Intelligence & Results Viewer',
    description:
      'Front-end results viewer for Pakistani electricity bills (K-Electric, LESCO, IESCO). Instant visual breakdown of charges, taxes, meter readings, and AI question answers.',
    images: ['/og-image.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
