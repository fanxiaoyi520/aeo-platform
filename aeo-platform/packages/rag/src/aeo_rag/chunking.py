"""Recursive character text splitter per M02 spec."""


def recursive_split(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    separators: list[str] | None = None,
) -> list[str]:
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    for sep in separators:
        if sep == "":
            chunks: list[str] = []
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                piece = text[start:end].strip()
                if piece:
                    chunks.append(piece)
                if end >= len(text):
                    break
                start = max(end - chunk_overlap, start + 1)
            return chunks

        if sep in text:
            parts = text.split(sep)
            chunks = []
            current = ""
            for i, part in enumerate(parts):
                piece = part if i == 0 else sep + part
                if len(current) + len(piece) <= chunk_size:
                    current += piece
                else:
                    if current.strip():
                        chunks.extend(
                            recursive_split(
                                current.strip(),
                                chunk_size,
                                chunk_overlap,
                                separators[separators.index(sep) + 1 :],
                            )
                        )
                    current = piece
            if current.strip():
                chunks.extend(
                    recursive_split(
                        current.strip(),
                        chunk_size,
                        chunk_overlap,
                        separators[separators.index(sep) + 1 :],
                    )
                )
            return [c for c in chunks if c.strip()]

    return [text[:chunk_size].strip()]
