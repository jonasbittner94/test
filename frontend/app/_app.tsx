"use client";
import type { AppProps } from "next/app";
import { FileProvider } from "@/context/FileContext";

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <FileProvider>
      <Component {...pageProps} />
    </FileProvider>
  );
}
