import type { Metadata } from "next";
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import "./globals.css";
import ThemeProvider from "../components/ThemeProvider";
import { ThresholdProvider } from "../lib/context/ThresholdContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MPC Plus",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} antialiased`}
        suppressHydrationWarning
      >
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const settings = localStorage.getItem('mpc-plus-settings');
                  const html = document.documentElement;
                  if (settings) {
                    const parsed = JSON.parse(settings);
                    if (parsed.theme === 'dark') {
                      html.classList.add('dark');
                    } else {
                      html.classList.remove('dark');
                    }
                    
                    if (parsed.accentColor && parsed.accentColor !== '#420039') {
                      html.style.setProperty('--primary', parsed.accentColor);
                      html.style.setProperty('--color-primary', parsed.accentColor);
                      html.style.setProperty('--ring', parsed.accentColor);
                    }
                  } else {
                    html.classList.remove('dark');
                  }
                } catch (e) {
                  document.documentElement.classList.remove('dark');
                }
              })();
            `,
          }}
        />
        <ThemeProvider>
          <ThresholdProvider>
            {children}
          </ThresholdProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
