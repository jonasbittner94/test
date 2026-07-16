"use client";
import type { ButtonHTMLAttributes } from "react";

type Variant =
  | "primary"
  | "secondary"
  | "success"
  | "danger"
  | "warning"
  | "info"
  | "light"
  | "dark"
  | "link";
type Size = "sm" | "lg";

type Props = {
  variant?: Variant;
  size?: Size;
  outline?: boolean;
  className?: string;
} & ButtonHTMLAttributes<HTMLButtonElement>;

export default function Button({
  variant = "primary",
  size,
  outline = false,
  className = "",
  ...props
}: Props) {
  const classes = [
    "btn",
    outline ? `btn-outline-${variant}` : `btn-${variant}`,
    size ? `btn-${size}` : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <button className={classes} {...props} />;
}
