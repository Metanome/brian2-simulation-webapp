"""
models.py - Neuron models for Brian2 Web Simulation

This file contains the neuron model classes and their equations for the Brian2 web interface.
"""

from brian2 import *

class LIFModel:
    """
    Leaky Integrate-and-Fire neuron model
    """
    @staticmethod
    def get_equations():
        """Return the equations for LIF model"""
        return '''
        dv/dt = (I - v) / (10*ms) : 1
        I : 1
        '''
    
    @staticmethod
    def get_threshold(threshold):
        """Return the threshold expression"""
        return f'v > {threshold}'
    
    @staticmethod
    def get_reset(reset):
        """Return the reset expression"""
        return f'v = {reset}'


class IzhikevichModel:
    """
    Izhikevich neuron model
    """
    @staticmethod
    def get_equations(a, b):
        """Return the equations for Izhikevich model"""
        return '''
        dv/dt = (0.04*v**2 + 5*v + 140 - u + I)/ms : 1
        du/dt = {a}*( {b}*v - u )/ms : 1
        I : 1
        '''.format(a=a, b=b)
    
    @staticmethod
    def get_threshold():
        """Return the threshold expression"""
        return 'v >= 30'
    
    @staticmethod
    def get_reset(c, d):
        """Return the reset expression"""
        return f'v = {c}; u += {d}'


class AdExModel:
    """
    Adaptive Exponential Integrate-and-Fire neuron model
    """
    @staticmethod
    def get_equations():
        """Return the equations for AdEx model"""
        return '''
        dv/dt = ( -gL*(v-EL) + gL*deltaT*exp((v-VT)/deltaT) - w + I ) / C : volt
        dw/dt = ( a*(v-EL) - w ) / tau_w : amp
        I : amp
        gL : siemens
        EL : volt
        deltaT : volt
        VT : volt
        a : siemens
        tau_w : second
        C : farad
        '''
    
    @staticmethod
    def get_threshold():
        """Return the threshold expression"""
        return 'v > VT'
    
    @staticmethod
    def get_reset(b):
        """Return the reset expression"""
        return f'v = EL; w += {b}*pA'
    
    @staticmethod
    def configure_group(G, input_current, deltaT, a, tau_w):
        """Configure AdEx neuron group parameters"""
        G.v = -65*mV
        G.w = 0*pA
        G.I = input_current * pA
        G.gL = 10*nS
        G.EL = -65*mV
        G.deltaT = deltaT * mV
        G.VT = -50*mV
        G.a = a * nS
        G.tau_w = tau_w * ms
        G.C = 200*pF
        return G


class CustomModel:
    """
    Custom neuron model with user-defined equations
    """
    @staticmethod
    def get_equations(eqs):
        """Return the user-defined equations"""
        return eqs
    
    @staticmethod
    def get_threshold(threshold):
        """Return the user-defined threshold expression"""
        return threshold
    
    @staticmethod
    def get_reset(reset):
        """Return the user-defined reset expression"""
        return reset