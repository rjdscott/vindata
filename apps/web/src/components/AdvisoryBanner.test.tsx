import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AdvisoryBanner } from "./AdvisoryBanner";

describe("<AdvisoryBanner />", () => {
  it("renders advisory wording", () => {
    render(<AdvisoryBanner />);
    expect(screen.getByRole("note")).toHaveTextContent(/Advisory only/i);
    expect(screen.getByRole("note")).toHaveTextContent(/decision support/i);
  });
});
