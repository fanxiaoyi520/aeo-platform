export type ListingDraft = {
  title: string;
  bullets: string[];
  search_terms: string;
  description: string;
};

export function emptyListingDraft(): ListingDraft {
  return {
    title: "",
    bullets: ["", "", "", "", ""],
    search_terms: "",
    description: "",
  };
}

export function listingFromGenerated(source: Record<string, unknown> | null | undefined): ListingDraft {
  if (!source) return emptyListingDraft();
  const bullets = Array.isArray(source.bullets)
    ? source.bullets.map((item) => String(item))
    : [];
  while (bullets.length < 5) {
    bullets.push("");
  }
  return {
    title: typeof source.title === "string" ? source.title : "",
    bullets: bullets.slice(0, 5),
    search_terms: typeof source.search_terms === "string" ? source.search_terms : "",
    description: typeof source.description === "string" ? source.description : "",
  };
}

export function listingToPayload(draft: ListingDraft): Record<string, unknown> {
  return {
    title: draft.title.trim(),
    bullets: draft.bullets.map((bullet) => bullet.trim()).filter(Boolean),
    search_terms: draft.search_terms.trim(),
    description: draft.description.trim(),
  };
}
