"use client";

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export function Toggle({ checked, onChange, label, disabled = false }: ToggleProps) {
  return (
    <label
      className={`flex items-center gap-3 ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}`}
    >
      <button
        aria-checked={checked}
        className={`relative h-6 w-11 rounded-full transition-colors duration-200 ${
          checked ? "bg-ink" : "bg-slate-300"
        } ${disabled ? "pointer-events-none" : ""}`}
        disabled={disabled}
        onClick={(e) => {
          e.preventDefault();
          if (!disabled) onChange(!checked);
        }}
        role="switch"
        type="button"
      >
        <span
          className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200 ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
      {label ? <span className="select-none text-sm text-slate-700">{label}</span> : null}
    </label>
  );
}
