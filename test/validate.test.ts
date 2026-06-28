import { describe, expect, test } from "bun:test";
import {
  validateCuries,
  registrySet,
  classBase,
  isValidCurie,
  type CometRegistry,
} from "../tools/validate-curies.ts";
import registry from "../registry/comet-curies.json" with { type: "json" };

const allow = registrySet(registry as unknown as CometRegistry);

describe("TS CURIE validator", () => {
  test("registry is non-trivial", () => {
    expect(allow.size).toBeGreaterThan(200);
  });

  test("known-good CURIEs validate", () => {
    const r = validateCuries(
      ["comet:Process", "comet-pcf:FunctionalUnit", "comet-pcr:PCRDocument", "comet-pcr:governedByPCR"],
      allow,
    );
    expect(r.invalid).toEqual([]);
  });

  test("the three pcrbase bugs are flagged", () => {
    const r = validateCuries(
      ["comet-core:GeographyScope", "comet:FunctionalUnit", "comet-pcf:biogenicCarbon"],
      allow,
    );
    expect(r.invalid.sort()).toEqual(
      ["comet-core:GeographyScope", "comet-pcf:biogenicCarbon", "comet:FunctionalUnit"].sort(),
    );
  });

  test("corrected forms validate", () => {
    const r = validateCuries(
      ["comet-ef:GeographyScope", "comet-pcf:FunctionalUnit", "comet-pcf:BiogenicCarbon"],
      allow,
    );
    expect(r.invalid).toEqual([]);
  });

  test("classBase strips the property suffix", () => {
    expect(classBase("comet-pcf:FunctionalUnit.referenceFlow")).toBe("comet-pcf:FunctionalUnit");
  });

  test("property-base leniency can be disabled", () => {
    // a made-up property whose class exists: lenient passes, strict fails
    expect(isValidCurie("comet-pcf:FunctionalUnit.madeUpProp", allow, true)).toBe(true);
    expect(isValidCurie("comet-pcf:FunctionalUnit.madeUpProp", allow, false)).toBe(false);
  });

  test("null/undefined are ignored", () => {
    expect(validateCuries([null, undefined, "comet:Process"], allow).valid).toEqual(["comet:Process"]);
  });
});
