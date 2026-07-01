import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-semibold transition-transform duration-200 disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-signal text-ink shadow-panel hover:-translate-y-0.5",
        variant === "secondary" && "bg-mint text-ink hover:-translate-y-0.5",
        variant === "ghost" && "border border-white/20 bg-white/5 text-cloud hover:bg-white/10",
        className
      )}
      {...props}
    />
  );
}
