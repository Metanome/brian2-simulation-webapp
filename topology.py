"""
Network topology implementations for Brian2 Web Simulation using NetworkX.
This module provides different connection patterns for neural networks.
"""

from brian2 import *
import numpy as np
import networkx as nx

def create_random_connections(neurons, weight, probability):
    """Create random connections (Erdős–Rényi model) using NetworkX."""
    N = len(neurons)
    G = nx.erdos_renyi_graph(N, probability, directed=True)
    
    # Create synapses based on neuron type
    if hasattr(neurons[0], 'v'):
        syn = Synapses(neurons, neurons, on_pre=f'v_post += {weight}', delay=1*ms)
    else:
        syn = Synapses(neurons, neurons, on_pre=f'I_post += {weight}*pA', delay=1*ms)
    
    # Connect synapses based on NetworkX graph
    edges = list(G.edges())
    if edges:
        i_arr = np.array([e[0] for e in edges], dtype=np.int32)
        j_arr = np.array([e[1] for e in edges], dtype=np.int32)
        syn.connect(i=i_arr, j=j_arr)
    else:
        # If there are no edges, set the synapses to inactive
        syn.active = False
    
    return syn, G  # Return both the synapses and the graph

def create_small_world_connections(neurons, weight, k=2, p_rewire=0.1):
    """Create small-world connectivity (Watts-Strogatz model) using NetworkX."""
    N = len(neurons)
    k = max(2, int(k))
    if k % 2 != 0:
        k += 1  # Make k even
        
    G = nx.watts_strogatz_graph(N, k, p_rewire)
    
    # Create synapses
    if hasattr(neurons[0], 'v'):
        syn = Synapses(neurons, neurons, on_pre=f'v_post += {weight}', delay=1*ms)
    else:
        syn = Synapses(neurons, neurons, on_pre=f'I_post += {weight}*pA', delay=1*ms)
    
    # Connect synapses based on NetworkX graph
    edges = list(G.edges())
    if edges:
        i_arr = np.array([e[0] for e in edges], dtype=np.int32)
        j_arr = np.array([e[1] for e in edges], dtype=np.int32)
        syn.connect(i=i_arr, j=j_arr)
    else:
        # If there are no edges, set the synapses to inactive
        syn.active = False    
    
    return syn, G  # Return both the synapses and the graph

def create_scale_free_connections(neurons, weight, m=2):
    """Create scale-free network (Barabási–Albert model) using NetworkX."""
    N = len(neurons)
    m = max(1, min(int(m), N//2))
    
    # NetworkX implementation
    G = nx.barabasi_albert_graph(N, m)
    
    # Create synapses
    if hasattr(neurons[0], 'v'):
        syn = Synapses(neurons, neurons, on_pre=f'v_post += {weight}', delay=1*ms)
    else:
        syn = Synapses(neurons, neurons, on_pre=f'I_post += {weight}*pA', delay=1*ms)
    
    # Connect synapses based on NetworkX graph
    edges = list(G.edges())
    if edges:
        i_arr = np.array([e[0] for e in edges], dtype=np.int32)
        j_arr = np.array([e[1] for e in edges], dtype=np.int32)
        syn.connect(i=i_arr, j=j_arr)
    else:
        # If there are no edges, set the synapses to inactive
        syn.active = False
    
    return syn, G  # Return both the synapses and the graph


def create_regular_lattice(neurons, weight, k=2):
    """Create regular lattice connectivity using NetworkX."""
    k = max(2, int(k))
    N = len(neurons)
    
    # Ensure k is even for consistency with the original implementation
    if k % 2 != 0:
        k += 1
    
    # Create a circulant graph where each node connects to k nearest neighbors
    # This creates a ring lattice with k/2 neighbors on each side
    G = nx.circulant_graph(N, [j for j in range(1, k//2 + 1)])
    
    # Create synapses
    if hasattr(neurons[0], 'v'):
        syn = Synapses(neurons, neurons, on_pre=f'v_post += {weight}', delay=1*ms)
    else:
        syn = Synapses(neurons, neurons, on_pre=f'I_post += {weight}*pA', delay=1*ms)
    
    # Connect synapses based on NetworkX graph
    edges = list(G.edges())
    if edges:
        i_arr = np.array([e[0] for e in edges], dtype=np.int32)
        j_arr = np.array([e[1] for e in edges], dtype=np.int32)
        syn.connect(i=i_arr, j=j_arr)
    else:
        # If there are no edges, set the synapses to inactive
        syn.active = False    
    
    return syn, G  # Return both the synapses and the graph


def create_modular_connections(neurons, weight, n_modules=4, p_intra=0.2, p_inter=0.01):
    """Create modular network connectivity using NetworkX."""
    N = len(neurons)
    n_modules = max(2, min(int(n_modules), N//2))
    
    # Calculate module sizes
    neurons_per_module = N // n_modules
    remainder = N % n_modules
    sizes = [neurons_per_module + (1 if i < remainder else 0) for i in range(n_modules)]
    
    # Create probability matrix where:
    # - Diagonal blocks have p_intra probability (intra-module connections)
    # - Off-diagonal blocks have p_inter probability (inter-module connections)
    p_matrix = np.ones((n_modules, n_modules)) * p_inter
    np.fill_diagonal(p_matrix, p_intra)
    
    # Create the stochastic block model
    G = nx.stochastic_block_model(sizes, p_matrix, directed=True)
    
    # Create synapses
    if hasattr(neurons[0], 'v'):
        syn = Synapses(neurons, neurons, on_pre=f'v_post += {weight}', delay=1*ms)
    else:
        syn = Synapses(neurons, neurons, on_pre=f'I_post += {weight}*pA', delay=1*ms)
    
    # Connect synapses based on NetworkX graph
    edges = list(G.edges())
    if edges:
        i_arr = np.array([e[0] for e in edges], dtype=np.int32)
        j_arr = np.array([e[1] for e in edges], dtype=np.int32)
        syn.connect(i=i_arr, j=j_arr)
    else:
        # If there are no edges, set the synapses to inactive
        syn.active = False    
    
    return syn, G  # Return both the synapses and the graph