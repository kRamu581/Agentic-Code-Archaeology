import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Dashboard from "./Dashboard";
import History from "./History";
import Compare from "./Compare";

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    isAxiosError: (error: unknown) => typeof error === "object" && error !== null && "isAxiosError" in error,
  },
}));

const mockedAxios = vi.mocked(axios);

function renderRoute(component: React.ReactNode) {
  return render(<MemoryRouter>{component}</MemoryRouter>);
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { connected: false, oauth_configured: false } });
  });

  it("renders repository analysis and validates an empty URL inline", async () => {
    renderRoute(<Dashboard />);
    expect(await screen.findByRole("heading", { name: "Agentic Code Archaeology" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Analyze Repository" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Enter a GitHub repository URL");
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });
});

describe("History", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url === "/api/analysis-history") {
        return Promise.resolve({ data: [{
          id: 7,
          github_url: "https://github.com/demo/sample",
          created_at: "2026-10-14T10:00:00Z",
          status: "complete",
          final_report: "Saved report",
        }] });
      }
      return Promise.resolve({ data: {
        analysis_id: 7,
        repository: "https://github.com/demo/sample",
        final_report: "Loaded without a new analysis",
      } });
    });
  });

  it("shows an empty state", async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: [] });
    renderRoute(<History />);
    expect(await screen.findByText("No repository analyses yet.")).toBeInTheDocument();
  });

  it("reloads the saved result by ID without posting a new analysis", async () => {
    renderRoute(<History />);
    expect(await screen.findByText("demo/sample")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "View saved analysis" }));
    expect(await screen.findByText("Loaded without a new analysis")).toBeInTheDocument();
    expect(mockedAxios.get).toHaveBeenCalledWith("/api/analysis-history/7");
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });
});

describe("Compare", () => {
  beforeEach(() => vi.clearAllMocks());

  it("rejects fewer than two repositories with a visible error", async () => {
    renderRoute(<Compare />);
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 1" }), {
      target: { value: "https://github.com/demo/one" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Compare Projects" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("at least two");
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  it("rejects duplicate repositories before making a request", async () => {
    renderRoute(<Compare />);
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 1" }), {
      target: { value: "https://github.com/demo/one" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 2" }), {
      target: { value: "https://github.com/demo/one.git/" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Compare Projects" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("more than once");
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  it("renders repository ranking and measured indicators", async () => {
    mockedAxios.post.mockResolvedValue({
      data: {
        repositories: [{
          repository: "https://github.com/demo/active",
          repository_name: "active",
          status: "complete",
          health_score: 87,
          todo_count: 2,
          metrics: { git_activity: 90, code_completeness: 90, recovery_potential: 80 },
        }],
        rankings: [],
        recommended_repository: {
          repository_name: "active",
          health_score: 87,
        },
      },
    });
    renderRoute(<Compare />);
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 1" }), {
      target: { value: "https://github.com/demo/active" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 2" }), {
      target: { value: "https://github.com/demo/old" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Compare Projects" }));
    await waitFor(() => expect(mockedAxios.post).toHaveBeenCalled());
    expect(await screen.findByText("87/100")).toBeInTheDocument();
    expect(screen.getByText("Highest measured viability")).toBeInTheDocument();
  });

  it("shows backend validation details without crashing on array-shaped errors", async () => {
    mockedAxios.post.mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: [{ msg: "Value error, Repository is unavailable." }] } },
    });
    renderRoute(<Compare />);
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 1" }), {
      target: { value: "https://github.com/demo/one" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Repository 2" }), {
      target: { value: "https://github.com/demo/two" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Compare Projects" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Repository is unavailable.");
  });
});
