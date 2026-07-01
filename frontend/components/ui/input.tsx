import { InputHTMLAttributes } from "react";
import clsx from "clsx";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={clsx(
        "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-cloud outline-none ring-0 placeholder:text-cloud/45 focus:border-mint/60",
        className
      )}
      {...props}
    />
  );
}
