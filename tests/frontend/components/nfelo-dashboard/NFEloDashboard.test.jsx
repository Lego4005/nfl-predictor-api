import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { vi } from "vitest";
import NFEloDashboard from "../../../../src/components/nfelo-dashboard/NFEloDashboard";

// Mock the alert function
global.alert = vi.fn();

describe("NFEloDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders without crashing", () => {
    render(<NFEloDashboard />);

    // Check if the main title is rendered
    expect(screen.getByText("NFL Model Projections")).toBeInTheDocument();
  });

  test("renders 4-column layout structure", () => {
    render(<NFEloDashboard />);

    // Check if all 4 columns are rendered
    expect(screen.getByText("Thursday, Sep 25")).toBeInTheDocument();
    const sundayColumns = screen.getAllByText("Sunday, Sep 28");
    expect(sundayColumns).toHaveLength(2); // early and late columns
    expect(screen.getByText("Monday, Sep 29")).toBeInTheDocument();
  });

  test("displays week selector with default week 4", () => {
    render(<NFEloDashboard />);

    // Check if week selector is rendered
    expect(screen.getByText("Week")).toBeInTheDocument();

    // Check if the select element exists and has week 4 selected
    const weekSelect = screen.getByRole("combobox");
    expect(weekSelect).toBeInTheDocument();
    expect(weekSelect.value).toBe("4");
  });

  test("week navigation buttons work", () => {
    render(<NFEloDashboard />);

    const nextButton = screen.getByText("›");
    const prevButton = screen.getByText("‹");
    const weekSelect = screen.getByRole("combobox");

    // Test next week button
    fireEvent.click(nextButton);
    expect(weekSelect.value).toBe("5");

    // Test previous week button
    fireEvent.click(prevButton);
    expect(weekSelect.value).toBe("4");
  });

  test("displays game cards with correct information", () => {
    render(<NFEloDashboard />);

    // Check if game teams are displayed
    expect(screen.getByText("SEA (2-1)")).toBeInTheDocument();
    expect(screen.getByText("ARI (2-1)")).toBeInTheDocument();
    expect(screen.getByText("MIN (2-1)")).toBeInTheDocument();
    expect(screen.getByText("PIT (2-1)")).toBeInTheDocument();

    // Check if final score is displayed
    expect(screen.getByText("23")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();

    // Check if FINAL indicator is shown
    expect(screen.getByText(/FINAL/)).toBeInTheDocument();
  });

  test("displays +EV opportunities correctly", () => {
    render(<NFEloDashboard />);

    // Check if +EV badges are displayed
    const evBadges = screen.getAllByText("1 +EV");
    expect(evBadges).toHaveLength(2); // Sunday early and late columns

    // Check if +EV opportunity text is displayed
    const evOpportunities = screen.getAllByText("+EV Opportunity");
    expect(evOpportunities).toHaveLength(2); // CLE-DET and GB-DAL games
  });

  test("game cards are clickable and show alert", () => {
    render(<NFEloDashboard />);

    // Find a game card and click it
    const gameCard = screen.getByText("SEA (2-1)").closest("div");
    fireEvent.click(gameCard);

    // Check if alert was called with correct game URL
    expect(global.alert).toHaveBeenCalledWith(
      expect.stringContaining(
        "https://nfeloapp.com/games/sea-ari-box-score-week-04-2025/"
      )
    );
  });

  test("week dropdown changes update the displayed week", () => {
    render(<NFEloDashboard />);

    const weekSelect = screen.getByRole("combobox");

    // Change to week 10
    fireEvent.change(weekSelect, { target: { value: "10" } });
    expect(weekSelect.value).toBe("10");

    // Test clicking a game card shows correct week in URL
    const gameCard = screen.getByText("SEA (2-1)").closest("div");
    fireEvent.click(gameCard);

    expect(global.alert).toHaveBeenCalledWith(
      expect.stringContaining("week-10-2025")
    );
  });

  test("renders correct game times", () => {
    render(<NFEloDashboard />);

    // Check if various game times are displayed
    expect(screen.getByText("08:15 PM")).toBeInTheDocument();
    expect(screen.getByText("09:30 AM")).toBeInTheDocument();
    expect(screen.getByText("01:00 PM")).toBeInTheDocument();
    expect(screen.getByText("08:20 PM")).toBeInTheDocument();
    expect(screen.getByText("07:15 PM")).toBeInTheDocument();
  });
});
