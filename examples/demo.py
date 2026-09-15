"""Calls the MCP tool functions directly, the same code path an MCP client uses."""

from flakelens.server import analyze_test_history

for row in analyze_test_history("examples/history"):
    ci = row["confidence_interval"]
    print(f"{row['status']:14s} {row['test']:45s} {row['failures']:2d}/{row['runs']:<3d} ci=[{ci[0]:.2f},{ci[1]:.2f}]")
