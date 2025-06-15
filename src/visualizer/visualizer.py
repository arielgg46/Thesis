# visualizer.py

import os
import numpy as np
import json
import matplotlib.pyplot as plt

all_domains = ["blocksworld", "gripper", "floor-tile"]
domain_colors = {
    "blocksworld": "blue", 
    "gripper": "green", 
    "floor-tile": "red"
}

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


def plot_all_metrics_grid(filename: str, results_folder_path: str, confidence_intervals: dict = None):
    """
    Crea una imagen compuesta 2x2 con las 4 métricas: parseable, solvable, correct y objects_count_ok.
    También grafica los intervalos de confianza como bandas difusas.

    Args:
        filename: El nombre del archivo que contiene los datos de los resultados.
        results_folder_path: La ruta a la carpeta que contiene el archivo de resultados.
        confidence_intervals: Un diccionario con intervalos de confianza por métrica y agente.
    """
    filepath = os.path.join(results_folder_path, filename)
    data = load_agent_results(filepath)

    metrics = [
        ("objects_count_ok", "Correct Objects (%)", "Percentage of models with correct objects, per Agent", 100),
        ("parseable", "Paseability (%)", "Percentage of parseable models per Agent", 100),
        ("solvable", "Solvability (%)", "Percentage of solvable models per Agent", 100),
        ("correct", "Correctness (%)", "Percentage of correct models per Agent", 100),
        # ("objects_count_ok", "Objetos correctos (%)", "Porcentaje de modelos con Objetos correctos", 100),
        # ("parseable", "Validez Sintáctica (%)", "Porcentaje de modelos Sintácticamente válidos por Agente", 100),
        # ("solvable", "Solubilidad (%)", "Porcentaje de modelos Solubles por Agente", 100),
        # ("correct", "Correctitud (%)", "Porcentaje de modelos Correctos por Agente", 100),
    ]

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    axs = axs.flatten()

    for ax, (metric, ylabel, title, ymax) in zip(axs, metrics):
        agent_names, values = [], []
        for agent, info in data.items():
            if "planner" in agent:
                continue
            evals = []
            for dom in info.get('domains', {}).values():
                for prob in dom.get('problems', {}).values():
                    ev = prob.get('eval', {})
                    if metric in ev:
                        evals.append(ev[metric])
            total = len(evals)
            pct = (sum(evals) / total * 100) if total else 0
            agent_names.append(agent)
            values.append(pct)

        # Colores coherentes según nombre del agente
        colors = []
        for name in agent_names:
            rgb = [0, 0, 0.3]
            if "plus" in name:
                rgb[2] += 0.4
            if "orig" in name:
                rgb[2] += 0.3
            if "fsp" in name:
                rgb[0] += 0.7
            colors.append(tuple(rgb))

        bars = ax.bar(agent_names, values, color=colors)

        # Dibujar banda difusa para intervalo de confianza
        if confidence_intervals:
            for i, agent_name in enumerate(agent_names):
                if agent_name in confidence_intervals:
                    try:
                        lower, upper = confidence_intervals[agent_name][metrics.index((metric, ylabel, title, ymax))]
                        lower *= 100
                        upper *= 100
                        ax.fill_between(
                            [i - 0.4, i + 0.4],
                            [lower, lower],
                            [upper, upper],
                            color='black',
                            alpha=0.25,
                            zorder=3  # por encima de las barras
                        )
                    except IndexError:
                        continue

        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, ymax + 5)
        ax.set_xticks(range(len(agent_names)))
        ax.set_xticklabels(agent_names, rotation=45, ha='right')

        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{value:.2f}',
                ha='center',
                va='bottom',
                fontsize=9
            )

    output_path = os.path.join(results_folder_path, 'metrics_grid.png')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

# ------------------------------------------------------------------------------
# Generic helper for bar charts
# ------------------------------------------------------------------------------
import matplotlib.pyplot as plt

def _plot_bar(
    agent_names: list[str],
    values: list[float],
    ylabel: str,
    title: str,
    output_path: str,
    colors = None,
    ymax = None
):
    if colors == None:
        colors = ["skyblue"] * len(agent_names)
        for i in range(len(agent_names)):
            rgb = [0, 0, 0.3]
            if "plus" in agent_names[i]:
                rgb[2] += 0.4
            if "orig" in agent_names[i]:
                rgb[2] += 0.3
            if "fsp" in agent_names[i]:
                rgb[0] += 0.7
            if "planner" in agent_names[i]:
                rgb[1] += 0.5
            # if not ("plus" in agent_names[i] or "orig" in agent_names[i]):
            #     rgb[1] += 0.017 * len(agent_names[i])
            colors[i] = tuple(rgb)
            

    plt.figure(figsize=(10, 5))
    bars = plt.bar(agent_names, values, color=colors)
    plt.title(title)
    plt.ylabel(ylabel)
    if ymax is not None:
        plt.ylim(0, ymax+5)
    plt.xticks(rotation=45, ha='right')

    # Add value labels on top of each bar
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # x position: center of the bar
            height,                             # y position: top of the bar
            f'{value:.2f}',                    # formatted value with 2 decimals
            ha='center',                       # horizontal alignment
            va='bottom'                       # vertical alignment (just above the bar)
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


# ------------------------------------------------------------------------------
# Individual plotters for each metric
# ------------------------------------------------------------------------------

def plot_objects_count_ok(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems with correct object count by each agent.
    """
    metric = 'objects_count_ok'
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

    out = os.path.join(results_folder_path, 'objects_count_ok_by_agent.png')
    _plot_bar(
        agent_names, percents,
        ylabel='Correct Objects Count (%)',
        title='Percentage of Problems with correct Objects Count by Agent',
        output_path=out,
        ymax=100
    )

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
        output_path=out,
        ymax=100
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
        output_path=out,
        ymax=100
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
        output_path=out,
        ymax=100
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


def plot_parseable_by_domain(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems parseable by each agent.
    """
    # Colors for each bar
    colors = []

    metric = 'parseable'
    agent_names, percents = [], []
    for agent, info in data.items():
        dom_names = []
        i = 0
        for key in info.get('domains', {}).keys():
            dom_names.append(key)
        for dom in info.get('domains', {}).values():
            dom_name = dom_names[i]
            i += 1
            if dom_name == "blocksworld":
                colors.append("blue")
            elif dom_name == "gripper":
                colors.append("green")
            elif dom_name == "floor-tile":
                colors.append("red")
            evals = []
            for prob in dom.get('problems', {}).values():
                ev = prob.get('eval', {})
                if metric in ev:
                    evals.append(ev[metric])
            total = len(evals)
            pct = (sum(evals) / total * 100) if total else 0
            agent_names.append(f"{agent}_{i}")
            percents.append(pct)

    out = os.path.join(results_folder_path, 'parseable_by_agent_and_domain.png')
    _plot_bar(
        agent_names, percents,
        ylabel='Parseable (%)',
        title='Percentage of Problems Parseable by Agent and Domain',
        output_path=out,
        colors=colors,
        ymax=100
    )


def plot_domain_parseable(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems parseable by each agent for a specific domain.
    """
    global all_domains
    global domain_colors
    metric = 'parseable'
    for domain in all_domains:
        agent_names, percents = [], []
        for agent, info in data.items():
            evals = []
            # Access only the specified domain
            dom = info.get('domains', {}).get(domain)
            if dom:
                for prob in dom.get('problems', {}).values():
                    ev = prob.get('eval', {})
                    if metric in ev:
                        evals.append(ev[metric])
            total = len(evals)
            pct = (sum(evals) / total * 100) if total else 0
            agent_names.append(agent)
            percents.append(pct)

        out = os.path.join(results_folder_path, f'{metric}_by_agent_in_{domain}.png')
        _plot_bar(
            agent_names, percents,
            ylabel='{metric} (%)',
            title=f'Percentage of Problems {metric} by Agent in Domain "{domain}"',
            output_path=out,
            ymax=100,
            colors=domain_colors[domain]
        )

def plot_domain_solvable(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems solvable by each agent for a specific domain.
    """
    global all_domains
    global domain_colors
    metric = 'solvable'
    for domain in all_domains:
        agent_names, percents = [], []
        for agent, info in data.items():
            evals = []
            # Access only the specified domain
            dom = info.get('domains', {}).get(domain)
            if dom:
                for prob in dom.get('problems', {}).values():
                    ev = prob.get('eval', {})
                    if metric in ev:
                        evals.append(ev[metric])
            total = len(evals)
            pct = (sum(evals) / total * 100) if total else 0
            agent_names.append(agent)
            percents.append(pct)

        out = os.path.join(results_folder_path, f'{metric}_by_agent_in_{domain}.png')
        _plot_bar(
            agent_names, percents,
            ylabel='{metric} (%)',
            title=f'Percentage of Problems {metric} by Agent in Domain "{domain}"',
            output_path=out,
            ymax=100,
            colors=domain_colors[domain]
        )

def plot_domain_correct(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems correct by each agent for a specific domain.
    """
    global all_domains
    global domain_colors
    metric = 'correct'
    for domain in all_domains:
        agent_names, percents = [], []
        for agent, info in data.items():
            evals = []
            # Access only the specified domain
            dom = info.get('domains', {}).get(domain)
            if dom:
                for prob in dom.get('problems', {}).values():
                    ev = prob.get('eval', {})
                    if metric in ev:
                        evals.append(ev[metric])
            total = len(evals)
            pct = (sum(evals) / total * 100) if total else 0
            agent_names.append(agent)
            percents.append(pct)

        out = os.path.join(results_folder_path, f'{metric}_by_agent_in_{domain}.png')
        _plot_bar(
            agent_names, percents,
            ylabel='{metric} (%)',
            title=f'Percentage of Problems {metric} by Agent in Domain "{domain}"',
            output_path=out,
            ymax=100,
            colors=domain_colors[domain]
        )


def plot_parseable_by_abstraction(data: dict, results_folder_path: str):
    """
    Bar chart of % of problems parseable by each agent.
    """
    metric = 'parseable'
    for init_abs, goal_abs in [[0, 0], [0, 1], [1, 0], [1, 1]]:
        agent_names, percents = [], []
        for agent, info in data.items():
            evals = []
            for dom in info.get('domains', {}).values():
                for prob in dom.get('problems', {}).values():
                    if prob["init_is_abstract"] != init_abs or prob["goal_is_abstract"] != goal_abs:
                        continue
                    ev = prob.get('eval', {})
                    if metric in ev:
                        evals.append(ev[metric])
            total = len(evals)
            pct = (sum(evals) / total * 100) if total else 0
            agent_names.append(agent)
            percents.append(pct)

        abstraction_str = ["expl", "abs"]
        out = os.path.join(results_folder_path, f'{metric}_by_agent_in_{abstraction_str[init_abs]}_to_{abstraction_str[goal_abs]}.png')
        _plot_bar(
            agent_names, percents,
            ylabel=f'{metric} (%)',
            title=f'Percentage of Problems {metric} by Agent, {abstraction_str[init_abs]} to {abstraction_str[goal_abs]}',
            output_path=out,
            ymax=100
        )

def plot_planning(filename: str, results_folder_path: str, confidence_intervals: dict = None):
    """
    Bar chart of % of correct problems or valid plans by each agent.
    Includes confidence intervals if provided.

    Args:
        data: Diccionario con los resultados por agente.
        results_folder_path: Ruta a la carpeta donde guardar el gráfico.
        confidence_intervals: Diccionario con intervalos de confianza (por agente), 
                              donde cada valor es una tupla (lower, upper) en [0, 1].
    """
    filepath = os.path.join(results_folder_path, filename)
    data = load_agent_results(filepath)

    agent_names, percents = [], []
    for agent, info in data.items():
        evals = []
        for dom in info.get('domains', {}).values():
            for prob in dom.get('problems', {}).values():
                init_is_abstract = prob.get('init_is_abstract', {})
                goal_is_abstract = prob.get('goal_is_abstract', {})
                if init_is_abstract or goal_is_abstract:
                    continue
                ev = prob.get('eval', {})
                if 'correct' in ev:
                    evals.append(ev['correct'])
                if 'is_valid' in ev:
                    evals.append(ev['is_valid'])
        total = len(evals)
        pct = (sum(evals) / total * 100) if total else 0
        agent_names.append(agent)
        percents.append(pct)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Colores según nombre
    colors = []
    for name in agent_names:
        rgb = [0, 0, 0.3]
        if "plus" in name:
            rgb[2] += 0.4
        if "orig" in name:
            rgb[2] += 0.3
        if "fsp" in name:
            rgb[0] += 0.7
        if "planner" in name:
            rgb[1] += 0.5
        colors.append(tuple(rgb))

    bars = ax.bar(agent_names, percents, color=colors)

    # Intervalos de confianza
    if confidence_intervals:
        for i, agent_name in enumerate(agent_names):
            if agent_name in confidence_intervals:
                lower, upper = confidence_intervals[agent_name]
                lower *= 100
                upper *= 100
                ax.fill_between(
                    [i - 0.4, i + 0.4],
                    [lower, lower],
                    [upper, upper],
                    color='black',
                    alpha=0.25,
                    zorder=3
                )

    ax.set_ylabel('Valid plans (%)')
    ax.set_title('Percentage of valid plans by Agent in explicit tasks')
    ax.set_ylim(0, 105)
    ax.set_xticks(range(len(agent_names)))
    ax.set_xticklabels(agent_names, rotation=45, ha='right')

    for bar, value in zip(bars, percents):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{value:.2f}',
            ha='center',
            va='bottom',
            fontsize=9
        )

    plt.tight_layout()
    out = os.path.join(results_folder_path, 'valid_plans_by_agent.png')
    plt.savefig(out)
    plt.close()


# ------------------------------------------------------------------------------
# Plotters
# ------------------------------------------------------------------------------

PLOTTERS = [
    # plot_objects_count_ok,
    # plot_parseable,
    # plot_parseable_by_domain,
    # plot_domain_parseable,
    # plot_domain_solvable,
    # plot_domain_correct,
    # plot_parseable_by_abstraction,
    # plot_solvable,
    # plot_correct,
    # plot_token_consumption,
    # plot_total_generation_time,
    plot_planning
]
