import { HTMLAttributes } from "react";
import clsx from "clsx";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        "rounded-xl2 border border-white/10 bg-panel/80 p-5 text-cloud shadow-panel backdrop-blur",
        className
      )}
      {...props}
    />
  );
}
