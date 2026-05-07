import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LevelChip } from "./LevelChip";

describe("<LevelChip />", () => {
  it("shows the label for each level", () => {
    for (const level of ["low", "elevated", "high", "extreme"] as const) {
      const { unmount } = render(<LevelChip level={level} />);
      expect(screen.getByText(new RegExp(level, "i"))).toBeInTheDocument();
      unmount();
    }
  });
});
