"use client";
import "./styles/globals.css";
import "bootstrap/dist/css/bootstrap.min.css";
import SiteNavbar from "@/components/ui/navBar";

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
          {children}
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
