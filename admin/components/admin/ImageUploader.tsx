"use client";

import { useCallback, useRef, useState } from "react";

interface ImageUploaderProps {
  onUpload: (file: File) => Promise<void> | void;
  uploading?: boolean;
  label?: string;
  accept?: string;
}

export function ImageUploader({
  onUpload,
  uploading = false,
  label = "Drop image here",
  accept = "image/*",
}: ImageUploaderProps) {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
      await onUpload(file);
    },
    [onUpload],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file?.type.startsWith("image/")) {
        void handleFile(file);
      }
    },
    [handleFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) void handleFile(file);
      e.target.value = "";
    },
    [handleFile],
  );

  return (
    <div
      className={`relative flex min-h-[180px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed transition-colors ${
        dragging
          ? "border-ink bg-slate-100"
          : "border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-white"
      }`}
      onClick={() => !uploading && inputRef.current?.click()}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setDragging(false);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        accept={accept}
        className="hidden"
        disabled={uploading}
        onChange={handleChange}
        type="file"
      />

      {preview ? (
        <div className="relative h-full w-full overflow-hidden rounded-3xl">
          <img
            alt="Upload preview"
            className="h-full max-h-[170px] w-full object-contain p-3"
            src={preview}
          />
          <button
            className="absolute right-3 top-3 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm hover:bg-white"
            onClick={(e) => {
              e.stopPropagation();
              setPreview(null);
            }}
            type="button"
          >
            Change
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 p-8 text-center">
          <div className="rounded-2xl bg-white p-4 shadow-sm">
            <svg
              className="h-7 w-7 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">{label}</p>
            <p className="mt-1 text-xs text-slate-500">
              or <span className="text-steel underline">click to browse</span> · PNG, JPG, WEBP
            </p>
          </div>
        </div>
      )}

      {uploading ? (
        <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-white/75">
          <div className="flex flex-col items-center gap-2">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-ink border-t-transparent" />
            <p className="text-xs font-medium text-ink">Uploading…</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
