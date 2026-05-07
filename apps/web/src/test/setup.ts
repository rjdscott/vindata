// Vitest setup. Adds RTL matchers and stubs the things JSDOM doesn't provide.
import "@testing-library/jest-dom/vitest";

// MapLibre touches `window.URL.createObjectURL`; not needed for unit tests.
if (typeof window !== "undefined" && typeof URL.createObjectURL !== "function") {
  (URL as unknown as { createObjectURL: () => string }).createObjectURL = () =>
    "blob:stub";
}
