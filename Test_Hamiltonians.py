import math
import numpy as np
import pandas as pd

from Operators import Operator, Density_Matrix, \
                      Observable, Random_Operator, \
                      Random_Observable, Random_Density_Matrix, \
                      Commutator, \
                      Magnus_Expansion_1st_Term, \
                      Magnus_Expansion_2nd_Term

from Nuclear_Spin import Nuclear_Spin

from Hamiltonians import H_Zeeman, H_Quadrupole, \
                         V0, V1, V2, \
                         H_Single_Mode_Pulse, \
                         H_Multiple_Mode_Pulse, \
                         H_Pulse_IP

import hypothesis.strategies as st
from hypothesis import given, note

# Checks that the Observable object returned by the method H_Zeeman changes sign when the angular
# coordinates of the magnetic field undergo the following change
# theta -> pi - theta    phi -> phi + pi
@given(par = st.lists(st.floats(min_value=0, max_value=20), min_size=3, max_size=3))
def test_Zeeman_Hamiltonian_Flipped_Magnetic_Field(par):
    spin = Nuclear_Spin()
    h_z1 = H_Zeeman(spin, par[0], par[1], par[2])
    h_z2 = H_Zeeman(spin, math.pi-par[0], par[1]+math.pi, par[2])
    note("H_Zeeman(theta, phi) = %r" % (h_z1.matrix))
    note("H_Zeeman(pi-theta, phi+pi) = %r" % (h_z2.matrix))
    note("H_Zeeman(pi-theta, phi+pi)+H_Zeeman(theta, phi) = %r" % (np.absolute(h_z1.matrix+h_z2.matrix)))
    assert np.all(np.absolute(h_z1.matrix+h_z2.matrix) < 1e-10)
    
# Checks that the object returned by the method H_Quadrupole is independent of the Euler angle gamma when
# the asymmetry parameter eta=0
@given(gamma = st.lists(st.floats(min_value=0, max_value=2*math.pi), min_size=2, max_size=2))
def test_Symmetrical_EFG(gamma):
    spin = Nuclear_Spin()
    h_q1 = H_Quadrupole(spin, 1, 0, 1, 1, gamma[0])
    h_q2 = H_Quadrupole(spin, 1, 0, 1, 1, gamma[1])
    note("H_Quadrupole(gamma1) = %r" % (h_q1.matrix))
    note("H_Quadrupole(gamma2) = %r" % (h_q2.matrix))
    assert np.all(np.absolute(h_q1.matrix-h_q2.matrix) < 1e-10)
    
# Checks that the formula for V^0 reduces to the 1/2 when the Euler angles are set to 0
@given(eta = st.floats(min_value=0, max_value=1))
def test_V0_Reduces_To_Half(eta):
    v0 = V0(eta, 0, 0, 0)
    assert math.isclose(1/2, v0, rel_tol=1e-10)
    
# Checks that the formula for V^{+/-1} reduces to 0 when the Euler angles are set to 0
def test_V1_Reduces_To_0():
    for sign in [-1, +1]:
        v1 = V1(sign, 0.5, 0, 0, 0)
        assert np.absolute(v1) < 1e-10
        
# Checks that the formula for V^{+/-2} reduces to
# (1/(2*sqrt(6)))*eta
# when the Euler angles are set to 0
@given(eta = st.floats(min_value=0, max_value=1))
def test_V2_Reduces_To_eta(eta):
    for sign in [-2, +2]:
        v2 = V2(sign, eta, 0, 0, 0)
        assert np.isclose(v2, eta/(2*math.sqrt(6)), rtol=1e-10)
        
# Checks that the Hamiltonians returned by H_Single_Mode_Pulse at times which differ by an integer
# multiple of the period of the electromagnetic wave is the same
@given(n = st.integers(min_value=-20, max_value=20))
def test_Periodical_Pulse_Hamiltonian(n):
    spin = Nuclear_Spin(1., 1.)
    omega = 5.
    t1 = 1.
    t2 = t1 + n*(2*math.pi)/omega
    h_p1 = H_Single_Mode_Pulse(spin, omega, 10., 0, math.pi/2, 0, t1)
    h_p2 = H_Single_Mode_Pulse(spin, omega, 10., 0, math.pi/2, 0, t2)
    note("H_Single_Mode_Pulse(t1) = %r" % (h_p1.matrix))
    note("H_Single_Mode_Pulse(t2) = %r" % (h_p2.matrix))
    assert np.all(np.isclose(h_p1.matrix, h_p2.matrix, rtol=1e-10))
    
# Checks that the superposition of two orthogonal pulses with the same frequency and a phase difference
# of pi/2 is equivalent to the time-reversed superposition of the two same pulses with one of them
# changed by sign
@given(t = st.floats(min_value=0, max_value=20))
def test_Time_Reversal_Equivalent_Opposite_Circular_Polarization(t):
    spin = Nuclear_Spin(1., 1.)
    mode_forward = pd.DataFrame([(5., 10., 0., 0., 0.),
                                 (5., 10., math.pi/2, math.pi/2, 0.)], 
                                columns=['frequency', 'amplitude', 'phase', 'theta', 'phi'])
    mode_backward = pd.DataFrame([(5., 10., 0., 0., 0.),
                                  (5., 10., -math.pi/2, math.pi/2, 0.)], 
                                 columns=['frequency', 'amplitude', 'phase', 'theta', 'phi'])
    h_p_forward = H_Multiple_Mode_Pulse(spin, mode_forward, t)
    h_p_backward = H_Multiple_Mode_Pulse(spin, mode_backward, -t)
    assert np.all(np.isclose(h_p_forward.matrix, h_p_backward.matrix, rtol=1e-10))
    
# Checks that the Hamiltonian of the pulse expressed in the interaction picture is equal to that in the
# Schroedinger picture when this latter commutes with the operator for the change of picture
def test_Invariant_IP_Pulse_Hamiltonian_When_Commutation_Holds():
    spin = Nuclear_Spin(1., 1.)
    mode = pd.DataFrame([(5., 10., 0., math.pi/2, 0.)], 
                        columns=['frequency', 'amplitude', 'phase', 'theta', 'phi'])
    h_change_of_picture = 5.*spin.I['x']
    h_pulse = H_Multiple_Mode_Pulse(spin, mode, 10.)
    h_pulse_ip = H_Pulse_IP(spin, mode, 10., h_change_of_picture)
    assert np.all(np.isclose(h_pulse.matrix, h_pulse_ip.matrix, rtol=1e-10))

    
    
    
    
    
    