"use client";

import React from "react";
import { FileProvider } from "@/context/FileContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  return <FileProvider>{children}</FileProvider>;
}
