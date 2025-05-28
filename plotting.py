"""
plotting.py - Plotting utilities for Brian2 Web Simulation

This file contains plotting functions for generating visualizations of simulation results.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.io as pio
from brian2 import ms, mV
import networkx as nx


def generate_static_voltage_plot(M, num_neurons, output_folder, filename):
    """
    Generate and save a static voltage plot using Matplotlib
    
    Parameters
    ----------
    M : StateMonitor
        Brian2 StateMonitor with recorded membrane potentials
    num_neurons : int
        Number of neurons in the simulation
    output_folder : str
        Path to the output folder
    filename : str
        Filename for the saved plot
        
    Returns
    -------
    str
        URL to the saved image
    """
    plt.figure(figsize=(10, 4))
    for i in range(num_neurons):
        plt.plot(M.t/ms, M.v[i], label=f'Neuron {i}')
    plt.xlabel('Time (ms)')
    plt.ylabel('Membrane potential (v)')
    plt.title('Membrane Potential Over Time')
    plt.legend()
    plt.tight_layout()
    img_path = os.path.join(output_folder, filename)
    plt.savefig(img_path)
    img_url = f'/output/{filename}'
    plt.close()
    return img_url


def generate_static_raster_plot(spike_mon, output_folder, filename):
    """
    Generate and save a static raster plot using Matplotlib
    
    Parameters
    ----------
    spike_mon : SpikeMonitor
        Brian2 SpikeMonitor with recorded spike times
    output_folder : str
        Path to the output folder
    filename : str
        Filename for the saved plot
        
    Returns
    -------
    str
        URL to the saved image
    """
    plt.figure(figsize=(10, 4))
    plt.plot(spike_mon.t/ms, spike_mon.i, '.k')
    plt.xlabel('Time (ms)')
    plt.ylabel('Neuron index')
    plt.title('Spike Raster Plot')
    plt.tight_layout()
    raster_path = os.path.join(output_folder, filename)
    plt.savefig(raster_path)
    raster_url = f'/output/{filename}'
    plt.close()
    return raster_url


def generate_interactive_voltage_plot(M, num_neurons):
    """
    Generate an interactive voltage plot using Plotly
    
    Parameters
    ----------
    M : StateMonitor
        Brian2 StateMonitor with recorded membrane potentials
    num_neurons : int
        Number of neurons in the simulation
        
    Returns
    -------
    str
        HTML string of the interactive plot
    """
    traces = []
    for i in range(num_neurons):
        traces.append(go.Scatter(
            x=(M.t/ms),
            y=M.v[i],
            mode='lines',
            name=f'Neuron {i}'
        ))
    layout = go.Layout(
        title='Membrane Potential Over Time',
        xaxis=dict(title='Time (ms)'),
        yaxis=dict(title='Membrane potential (v)'),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,  # places legend below the x-axis label
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=40, r=20, t=40, b=60),  # increase bottom margin for legend
        height=350
    )
    fig = go.Figure(data=traces, layout=layout)
    return pio.to_html(fig, full_html=False)


def generate_interactive_raster_plot(spike_mon):
    """
    Generate an interactive raster plot using Plotly
    
    Parameters
    ----------
    spike_mon : SpikeMonitor
        Brian2 SpikeMonitor with recorded spike times
        
    Returns
    -------
    str
        HTML string of the interactive plot
    """
    trace = go.Scatter(
        x=(spike_mon.t/ms),
        y=spike_mon.i,
        mode='markers',
        marker=dict(color='black', size=6),
        showlegend=False
    )
    layout = go.Layout(
        title='Spike Raster Plot',
        xaxis=dict(title='Time (ms)'),
        yaxis=dict(title='Neuron index'),
        margin=dict(l=40, r=20, t=40, b=40),
        height=350
    )
    fig = go.Figure(data=[trace], layout=layout)
    return pio.to_html(fig, full_html=False)


def generate_network_topology_plot(G, output_folder, filename):
    """
    Generate and save a network topology visualization using NetworkX and Matplotlib
    
    Parameters
    ----------
    G : networkx.Graph
        NetworkX graph representing the network topology
    output_folder : str
        Path to the output folder
    filename : str
        Filename for the saved plot
        
    Returns
    -------
    str
        URL to the saved image
    """
    plt.figure(figsize=(8, 8))
    pos = nx.spring_layout(G, seed=42)  # Consistent layout between runs
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=500, font_size=10, font_weight='bold',
            edge_color='gray', arrows=True)
    plt.title('Network Topology')
    topology_path = os.path.join(output_folder, filename)
    plt.savefig(topology_path)
    topology_url = f'/output/{filename}'
    plt.close()
    return topology_url


def generate_interactive_topology_plot(G):
    """
    Generate an interactive network topology plot using Plotly
    
    Parameters
    ----------
    G : networkx.Graph
        NetworkX graph representing the network topology
        
    Returns
    -------
    str
        HTML string of the interactive plot
    """
    # Get positions using NetworkX's layout algorithm
    pos = nx.spring_layout(G, seed=42)
    
    # Create edges
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')
    
    # Create nodes
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[str(i) for i in G.nodes()],
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='lightblue',
            size=10,
            line_width=2))
    
    # Create figure
    layout = go.Layout(
        title='Network Topology',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500
    )
    
    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
    return pio.to_html(fig, full_html=False)