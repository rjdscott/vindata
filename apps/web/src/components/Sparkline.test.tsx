import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Sparkline } from "./Sparkline";

describe("<Sparkline />", () => {
  it("renders n/a placeholder for empty/insufficient data", () => {
    render(<Sparkline values={[]} ariaLabel="empty" />);
    expect(screen.getByLabelText("empty")).toHaveTextContent("n/a");
  });

  it("renders a polyline for valid numeric series", () => {
    const { container } = render(
      <Sparkline values={[0, 0.2, 0.5, 0.8]} ariaLabel="trend" />,
    );
    const poly = container.querySelector("polyline");
    expect(poly).not.toBeNull();
    // Four points → at least 3 commas in the points attribute (n-1 segments).
    expect((poly?.getAttribute("points") ?? "").split(" ")).toHaveLength(4);
  });

  it("renders a horizontal reference line when referenceY is in range", () => {
    const { container } = render(
      <Sparkline values={[10, 30, 50]} referenceY={20} domain={[0, 50]} />,
    );
    const ref = container.querySelector("line");
    expect(ref).not.toBeNull();
    expect(ref?.getAttribute("stroke-dasharray")).toBe("2 2");
  });
});
