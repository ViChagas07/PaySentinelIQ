"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { FileSearch } from "lucide-react";

export default function DocumentsPage() {
  return (
    <PagePlaceholder
      title="Document Analysis"
      description="Deep-dive document forensics with OCR, metadata analysis, forgery detection, and AI-powered content verification."
      icon={<FileSearch className="h-8 w-8" />}
      badge="AI Analysis"
      badgeVariant="primary"
    />
  );
}
