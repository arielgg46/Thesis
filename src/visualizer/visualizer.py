# visualizer.py

import os
import json
import matplotlib.pyplot as plt

def load_agent_results(filepath: str) -> dict:
    """
    Load the JSON results by-agent.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def visualize_agent_evaluations(filename: str, results_folder_path: str):
    """
    Load a by-agent JSON file and invoke each registered plotter.
    """
    filepath = os.path.join(results_folder_path, filename)
    data = load_agent_results(filepath)

    # Call each plotting function in turn
    for plotter in PLOTTERS:
        plotter(data, results_folder_path)

# ------------------------------------------------------------------------------
# Generic helper for bar charts
# ------------------------------------------------------------------------------
def _plot_bar(
    agent_names: list[str],
    values: list[float],
    ylabel: str,
    title: str,
    output_path: str
):
    plt.figure(figsize=(10, 5))
    plt.bar(agent_names, values, color='skyblue')
    plt.title(title)
    plt.ylabel(ylabel)
    # plt.ylim(0, 100)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

# ------------------------------------------------------------------------------
# Individual plotters for each metric
# ------------------------------------------------------------------------------

def plot_parseable(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems parseable by each agent.
    """
    metric = 'parseable'
    agent_names, percents = [], []
    for agent, info in data.items():
        evals = []
        for dom in info.get('domains', {}).values():
            for prob in dom.get('problems', {}).values():
                ev = prob.get('eval', {})
                if metric in ev:
                    evals.append(ev[metric])
        total = len(evals)
        pct = (sum(evals) / total * 100) if total else 0
        agent_names.append(agent)
        percents.append(pct)

    out = os.path.join(results_folder_path, 'parseable_by_agent.png')
    _plot_bar(
        agent_names, percents,
        ylabel='Parseable (%)',
        title='Percentage of Problems Parseable by Agent',
        output_path=out
    )

def plot_solvable(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems solvable by each agent.
    """
    metric = 'solvable'
    agent_names, percents = [], []
    for agent, info in data.items():
        evals = []
        for dom in info.get('domains', {}).values():
            for prob in dom.get('problems', {}).values():
                ev = prob.get('eval', {})
                if metric in ev:
                    evals.append(ev[metric])
        total = len(evals)
        pct = (sum(evals) / total * 100) if total else 0
        agent_names.append(agent)
        percents.append(pct)

    out = os.path.join(results_folder_path, 'solvable_by_agent.png')
    _plot_bar(
        agent_names, percents,
        ylabel='Solvable (%)',
        title='Percentage of Problems Solvable by Agent',
        output_path=out
    )

def plot_correct(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems correct by each agent.
    """
    metric = 'correct'
    agent_names, percents = [], []
    for agent, info in data.items():
        evals = []
        for dom in info.get('domains', {}).values():
            for prob in dom.get('problems', {}).values():
                ev = prob.get('eval', {})
                if metric in ev:
                    evals.append(ev[metric])
        total = len(evals)
        pct = (sum(evals) / total * 100) if total else 0
        agent_names.append(agent)
        percents.append(pct)

    out = os.path.join(results_folder_path, 'correct_by_agent.png')
    _plot_bar(
        agent_names, percents,
        ylabel='Correct (%)',
        title='Percentage of Problems Correct by Agent',
        output_path=out
    )

def plot_token_consumption(data: dict, results_folder_path: str):
    """
    Bar chart of token consumption by each agent.
    """
    agent_names, tokens = [], []
    for agent, info in data.items():
        evals = []
        for dom in info.get('domains', {}).values():
            for prob in dom.get('problems', {}).values():
                ev = prob.get('eval', {})
                if "total_tokens" in ev:
                    evals.append(ev["total_tokens"][-1])
        total = len(evals)
        pct = (sum(evals)) if total else 0
        agent_names.append(agent)
        tokens.append(pct)

    out = os.path.join(results_folder_path, 'total_tokens_by_agent.png')
    _plot_bar(
        agent_names, tokens,
        ylabel='Total tokens',
        title='Total token consumption by Agent',
        output_path=out
    )

def plot_total_generation_time(data: dict, results_folder_path: str):
    """
    Bar chart of total generation time by each agent.
    """
    agent_names, tokens = [], []
    for agent, info in data.items():
        evals = []
        for dom in info.get('domains', {}).values():
            for prob in dom.get('problems', {}).values():
                if "generation_time" in prob:
                    evals.append(prob["generation_time"])
        total = len(evals)
        pct = (sum(evals)) if total else 0
        agent_names.append(agent)
        tokens.append(pct)

    out = os.path.join(results_folder_path, 'total_generation_time_by_agent.png')
    _plot_bar(
        agent_names, tokens,
        ylabel='Total Generation time',
        title='Total Generation time by Agent',
        output_path=out
    )

# ------------------------------------------------------------------------------
# Plotters
# ------------------------------------------------------------------------------

PLOTTERS = [
    plot_parseable,
    plot_solvable,
    plot_correct,
    plot_token_consumption,
    plot_total_generation_time
]
