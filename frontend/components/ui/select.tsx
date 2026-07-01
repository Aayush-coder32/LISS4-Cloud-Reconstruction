import { SelectHTMLAttributes } from "react";
import clsx from "clsx";

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={clsx(
        "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-cloud outline-none focus:border-mint/60",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}
