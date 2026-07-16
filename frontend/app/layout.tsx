"use client";
import type { Metadata } from "next";
import "./styles/globals.css";
import Providers from "./providers";
import "bootstrap/dist/css/bootstrap.min.css";
import SiteNavbar from "@/components/ui/navBar";

const metadata: Metadata = {
  title: "PackageFinder",
  description: "Your Tool to find the right packaging",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body>
        <header
          style={{
            padding: 12,
            borderBottom: "1px solid #eee",
            position: "relative",
          }}
        >
          <SiteNavbar />
        </header>

        <main style={{ maxWidth: 900, margin: "24px auto", padding: "0 16px" }}>
          <Providers>{children}</Providers>
        </main>

        <footer
          style={{
            padding: 12,
            borderTop: "1px solid #eee",
            textAlign: "center",
          }}
        >
          © {new Date().getFullYear()}
        </footer>
      </body>
    </html>
  );
}
