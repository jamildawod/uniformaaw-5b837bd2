import { forwardRef } from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, className = "", ...props },
  ref,
) {
  return (
    <label className="block space-y-1.5 text-sm">
      {label ? <span className="font-medium text-slate-700">{label}</span> : null}
      <input
        ref={ref}
        className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:ring-2 focus:ring-ink/10 ${
          error
            ? "border-red-400 focus:border-red-400"
            : "border-slate-200 focus:border-slate-400"
        } ${className}`}
        {...props}
      />
      {error ? <span className="text-xs text-red-600">{error}</span> : null}
      {!error && hint ? <span className="text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
});

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, error, hint, className = "", ...props },
  ref,
) {
  return (
    <label className="block space-y-1.5 text-sm">
      {label ? <span className="font-medium text-slate-700">{label}</span> : null}
      <textarea
        ref={ref}
        className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:ring-2 focus:ring-ink/10 ${
          error
            ? "border-red-400 focus:border-red-400"
            : "border-slate-200 focus:border-slate-400"
        } ${className}`}
        {...props}
      />
      {error ? <span className="text-xs text-red-600">{error}</span> : null}
      {!error && hint ? <span className="text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
});
