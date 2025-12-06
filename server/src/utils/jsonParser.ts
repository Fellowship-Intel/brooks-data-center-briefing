/**
 * Enhanced JSON parsing with robust error handling.
 */

/**
 * Extract JSON object from text that may contain markdown or extra text.
 * Handles common edge cases.
 */
export function extractJsonFromText(text: string): Record<string, any> | null {
  if (!text) {
    return null;
  }

  // Remove markdown code fences
  let cleaned = text.replace(/```json\s*/gi, '').replace(/```\s*/g, '');

  // Find JSON object boundaries
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');

  if (start === -1 || end === -1 || end <= start) {
    return null;
  }

  const jsonStr = cleaned.substring(start, end + 1);

  // Try to parse
  try {
    return JSON.parse(jsonStr);
  } catch (error) {
    // Try to fix common issues
    const fixed = fixCommonJsonIssues(jsonStr);
    try {
      return JSON.parse(fixed);
    } catch (parseError) {
      return null;
    }
  }
}

/**
 * Fix common JSON formatting issues.
 */
function fixCommonJsonIssues(jsonStr: string): string {
  // Remove trailing commas before closing braces/brackets
  let fixed = jsonStr.replace(/,\s*}/g, '}').replace(/,\s*]/g, ']');

  // Fix unescaped newlines in strings (basic attempt)
  // This is conservative - only fixes obvious cases
  fixed = fixed.replace(/(?<!\\)\n(?![\\"])/g, '\\n');

  return fixed;
}

/**
 * Parse JSON from Gemini response with robust error handling.
 * Raises Error if parsing fails.
 */
export function parseGeminiJsonResponse(text: string): Record<string, any> {
  if (!text) {
    throw new Error('Empty response text');
  }

  const parsed = extractJsonFromText(text);

  if (parsed === null) {
    // Log the problematic text for debugging
    const snippet = text.length > 500 ? text.substring(0, 500) : text;
    throw new Error(
      `Could not extract valid JSON from response. Response snippet: ${snippet}`
    );
  }

  return parsed;
}

