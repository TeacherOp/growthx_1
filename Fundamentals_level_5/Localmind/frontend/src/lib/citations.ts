/**
 * Citation Parser Utility
 * Educational Note: This utility parses citations from AI responses.
 * Claude uses the format [[cite:SOURCE_ID:PAGE]] to cite sources.
 * We parse these, assign numbers, and prepare data for rendering.
 */

/**
 * Parsed citation data
 */
export interface Citation {
  /** The full citation marker (e.g., [[cite:abc123:5]]) */
  marker: string;
  /** The source UUID */
  sourceId: string;
  /** The page number (1-indexed) */
  pageNumber: number;
  /** Assigned citation number for display (e.g., [1], [2]) */
  citationNumber: number;
}

/**
 * Unique citation entry for the sources footer
 */
export interface CitationEntry {
  /** Assigned citation number */
  citationNumber: number;
  /** The source UUID */
  sourceId: string;
  /** The page number */
  pageNumber: number;
  /** Source name (filled in after fetching) */
  sourceName?: string;
}

/**
 * Result of parsing citations from text
 */
export interface ParsedContent {
  /** Array of all citations found (in order of appearance) */
  citations: Citation[];
  /** Unique citation entries for footer (deduplicated) */
  uniqueCitations: CitationEntry[];
  /** Map of marker -> citation number for quick lookup */
  markerToNumber: Map<string, number>;
}

// Regex to match citation format: [[cite:SOURCE_ID:PAGE]]
// SOURCE_ID can contain alphanumeric chars, hyphens, and underscores
// PAGE is a positive integer
const CITATION_REGEX = /\[\[cite:([a-zA-Z0-9_-]+):(\d+)\]\]/g;

/**
 * Parse citations from AI response text
 *
 * Educational Note: This function extracts all citations from the text,
 * assigns sequential numbers to unique citations, and prepares data for
 * both inline rendering and the sources footer.
 *
 * @param text - The AI response text containing [[cite:...]] markers
 * @returns ParsedContent with citations, unique entries, and marker mapping
 */
export function parseCitations(text: string): ParsedContent {
  const citations: Citation[] = [];
  const uniqueCitations: CitationEntry[] = [];
  const markerToNumber = new Map<string, number>();

  // Track unique source+page combinations
  const seenKeys = new Map<string, number>();

  let match: RegExpExecArray | null;
  let citationCounter = 1;

  // Reset regex state
  CITATION_REGEX.lastIndex = 0;

  while ((match = CITATION_REGEX.exec(text)) !== null) {
    const marker = match[0];
    const sourceId = match[1];
    const pageNumber = parseInt(match[2], 10);

    // Create unique key for this source+page combination
    const uniqueKey = `${sourceId}:${pageNumber}`;

    let citationNumber: number;

    if (seenKeys.has(uniqueKey)) {
      // Reuse existing citation number for same source+page
      citationNumber = seenKeys.get(uniqueKey)!;
    } else {
      // Assign new citation number
      citationNumber = citationCounter++;
      seenKeys.set(uniqueKey, citationNumber);

      // Add to unique citations for footer
      uniqueCitations.push({
        citationNumber,
        sourceId,
        pageNumber,
      });
    }

    // Store marker -> number mapping
    markerToNumber.set(marker, citationNumber);

    // Add to citations array
    citations.push({
      marker,
      sourceId,
      pageNumber,
      citationNumber,
    });
  }

  return {
    citations,
    uniqueCitations,
    markerToNumber,
  };
}

/**
 * Check if text contains any citations
 *
 * @param text - The text to check
 * @returns true if text contains at least one citation
 */
export function hasCitations(text: string): boolean {
  CITATION_REGEX.lastIndex = 0;
  return CITATION_REGEX.test(text);
}

/**
 * Split text into segments (text and citation markers)
 *
 * Educational Note: This function splits the AI response into an array of
 * segments where each segment is either plain text or a citation marker.
 * This makes it easy to render the text with inline citation components.
 *
 * @param text - The AI response text
 * @returns Array of segments, each marked as 'text' or 'citation'
 */
export function splitTextWithCitations(
  text: string
): Array<{ type: 'text' | 'citation'; content: string; sourceId?: string; pageNumber?: number }> {
  const segments: Array<{
    type: 'text' | 'citation';
    content: string;
    sourceId?: string;
    pageNumber?: number;
  }> = [];

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  // Reset regex state
  CITATION_REGEX.lastIndex = 0;

  while ((match = CITATION_REGEX.exec(text)) !== null) {
    // Add text before this citation
    if (match.index > lastIndex) {
      segments.push({
        type: 'text',
        content: text.slice(lastIndex, match.index),
      });
    }

    // Add the citation
    segments.push({
      type: 'citation',
      content: match[0],
      sourceId: match[1],
      pageNumber: parseInt(match[2], 10),
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text after last citation
  if (lastIndex < text.length) {
    segments.push({
      type: 'text',
      content: text.slice(lastIndex),
    });
  }

  return segments;
}

/**
 * Remove all citation markers from text
 *
 * @param text - The text with citation markers
 * @returns Clean text without citation markers
 */
export function stripCitations(text: string): string {
  return text.replace(CITATION_REGEX, '');
}
