/**
 * TypeScript reference validator — checks COMET CURIEs against the shared registry.
 *
 * Consumed by CarbonSigProductHub/verifier-export. Vendor
 * `registry/comet-curies.json` into the consumer and import these helpers, or
 * run as a CLI under Bun.
 *
 * A CURIE is valid if it is an exact registry member, or (when
 * allowPropertyBase) its class base — the part before the first '.' in the local
 * name — is a member.
 */

export interface CometRegistry {
  comet_published: string[];
  comet_pcr_pending: string[];
  namespaces: Record<string, string>;
}

export function registrySet(registry: CometRegistry): Set<string> {
  return new Set([...registry.comet_published, ...registry.comet_pcr_pending]);
}

/** comet-pcf:FunctionalUnit.referenceFlow -> comet-pcf:FunctionalUnit */
export function classBase(curie: string): string {
  const i = curie.indexOf(":");
  if (i === -1) return curie;
  const prefix = curie.slice(0, i);
  const local = curie.slice(i + 1);
  return `${prefix}:${local.split(".")[0]}`;
}

export function isValidCurie(
  curie: string,
  allow: Set<string>,
  allowPropertyBase = true,
): boolean {
  if (allow.has(curie)) return true;
  if (allowPropertyBase && allow.has(classBase(curie))) return true;
  return false;
}

export interface ValidateResult {
  valid: string[];
  invalid: string[];
}

export function validateCuries(
  curies: (string | null | undefined)[],
  allow: Set<string>,
  allowPropertyBase = true,
): ValidateResult {
  const valid: string[] = [];
  const invalid: string[] = [];
  for (const c of curies) {
    if (c == null) continue;
    (isValidCurie(c, allow, allowPropertyBase) ? valid : invalid).push(c);
  }
  return { valid, invalid };
}

// ── CLI (Bun) ────────────────────────────────────────────────────────────────
if (import.meta.main) {
  const here = new URL(".", import.meta.url).pathname;
  const registry = JSON.parse(
    await Bun.file(`${here}../registry/comet-curies.json`).text(),
  ) as CometRegistry;
  const allow = registrySet(registry);

  const args = Bun.argv.slice(2);
  const curies =
    args.length === 1 && args[0] === "-"
      ? (JSON.parse(await Bun.stdin.text()) as string[])
      : args;

  const { valid, invalid } = validateCuries(curies, allow);
  for (const c of valid) console.log(`✓ ${c}`);
  for (const c of invalid) console.error(`✗ ${c}  (not in COMET registry)`);
  process.exit(invalid.length === 0 ? 0 : 1);
}
