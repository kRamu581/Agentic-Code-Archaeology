import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RepositoryGraph from "./RepositoryGraph";
import { getRepositoryNodeLabel, normalizeRepositoryGraph } from "./repositoryGraphData";

describe("RepositoryGraph", () => {
  it("formats commit tooltips with a short SHA and message and file tooltips with the path", () => {
    expect(getRepositoryNodeLabel({
      id: "commit-abcdef1234",
      label: "abcdef1234",
      message: "Fix graph rendering",
      type: "commit",
    })).toBe("abcdef1 - Fix graph rendering");
    expect(getRepositoryNodeLabel({
      id: "file-src/index.ts",
      label: "src/index.ts",
      type: "file",
    })).toBe("src/index.ts");
  });

  it("deduplicates file paths and connects each commit to the shared file node", () => {
    const graph = normalizeRepositoryGraph({
      nodes: [
        { id: "commit-a", label: "abc1234", message: "Add feature", type: "commit" },
        { id: "file-a", label: "src/index.ts", type: "file" },
        { id: "commit-b", label: "def5678", message: "Fix feature", type: "commit" },
        { id: "file-b", label: "src/index.ts", type: "file" },
      ],
      edges: [
        { source: "commit-a", target: "file-a" },
        { source: "commit-b", target: "file-b" },
        {
          source: { id: "commit-a", label: "abc1234", message: "Add feature", type: "commit" },
          target: { id: "file-b", label: "src/index.ts", type: "file" },
        },
      ],
    });

    expect(graph.nodes.filter((node) => node.type === "file")).toHaveLength(1);
    expect(graph.links).toEqual([
      { source: "commit-a", target: "file-a" },
      { source: "commit-b", target: "file-a" },
    ]);
  });

  it("shows a friendly empty state when there are no graph nodes", () => {
    render(<RepositoryGraph graphData={{ nodes: [], edges: [] }} />);
    expect(screen.getByText("No repository relationship data is available yet.")).toBeInTheDocument();
  });
});
