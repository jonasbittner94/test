"use client";

import Button from "@/components/ui/button";
import "bootstrap/dist/css/bootstrap.min.css";

import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>Was macht der PackageFinder</h1>
      <p>
        Der PackageFinder ist ein Tool, welches es vereinfacht die richtige
        Verpackung für einen Artikel zu Finden.
      </p>
      <img
        src="/verpackungBild.png"
        style={{
          width: "500px",
          height: "auto",
        }}
      ></img>
      <a href="/form">
        <Button variant="secondary">Verpackung für neuen Artikel suchen</Button>
      </a>
    </main>
  );
}
