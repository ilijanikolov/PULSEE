from Operators import Operator, Density_Matrix, \
                      Observable, random_operator, \
                      random_observable, random_density_matrix, \
                      Commutator, \
                      Magnus_Expansion_1st_Term, \
                      Magnus_Expansion_2nd_Term, \
                      Canonical_Density_Matrix

import math
from numpy import log
import numpy as np
from scipy import linalg
from scipy.linalg import eig
from scipy.integrate import quad
from scipy.constants import Planck, Boltzmann

import hypothesis.strategies as st
from hypothesis import given, note, assume

def test_operator_initialisation_with_wrong_dimensions():
    wrong_input = np.ones((1, 2))
    try:
        o = Operator(wrong_input)
        raise AssertionError
    except IndexError as e:
        if not "An Operator object should be initialised with a 2D square array" in e.args[0]:
            raise AssertionError("No appropriate IndexError caused by the initialisation with a non-square array")
    except AssertionError:
        raise AssertionError("No appropriate IndexError caused by the initialisation with a non-square array")

@given(d = st.integers(min_value=1, max_value=16))
def test_opposite_operator(d):
    o = random_operator(d)
    note("o = %r" % (o.matrix))
    assert np.all(np.isclose((o-o).matrix, np.zeros((d,d)), rtol=1e-10))

@given(d = st.integers(min_value=1, max_value=16))
def test_associativity_sum_operators(d):
    a = random_operator(d)
    b = random_operator(d)
    c = random_operator(d)
    left_sum = (a+b)+c
    right_sum = a+(b+c)
    note("a = %r" % (a.matrix))
    note("b = %r" % (b.matrix))
    note("c = %r" % (c.matrix))
    note("(a+b)+c = %r" % (left_sum.matrix))
    note("a+(b+c) = %r" % (right_sum.matrix))
    assert np.all(np.isclose(left_sum.matrix, right_sum.matrix, rtol=1e-10))

@given(d = st.integers(min_value=1, max_value=16))
def test_associativity_product_operators(d):
    a = random_operator(d)
    b = random_operator(d)
    c = random_operator(d)
    left_product = (a*b)*c
    right_product = a*(b*c)
    note("a = %r" % (a.matrix))
    note("b = %r" % (b.matrix))
    note("c = %r" % (c.matrix))
    note("(a*b)*c = %r" % (left_product.matrix))
    note("a*(b*c) = %r" % (right_product.matrix))
    assert np.all(np.isclose(left_product.matrix, right_product.matrix, rtol=1e-10))

@given(d = st.integers(min_value=1, max_value=16))
def test_distributivity_operators(d):
    a = random_operator(d)
    b = random_operator(d)
    c = random_operator(d)
    left_hand_side = a*(b+c)
    right_hand_side = a*b+a*c
    note("a = %r" % (a.matrix))
    note("b = %r" % (b.matrix))
    note("c = %r" % (c.matrix))
    note("a*(b+c) = %r" % (left_hand_side.matrix))
    note("a*b+a*c = %r" % (right_hand_side.matrix))
    assert np.all(np.isclose(left_hand_side.matrix, right_hand_side.matrix, rtol=1e-10))
    
@given(d = st.integers(min_value=1, max_value=16))
def test_operator_trace_normalisation(d):
    o = random_operator(d)
    o_trace = o.trace()
    o_norm = o/o_trace
    o_norm_trace = o_norm.trace()
    note("o = %r" % (o.matrix))
    note("Trace of o = %r" % (o_trace))
    note("Trace-normalised o = %r" % (o_norm))
    note("Trace of trace-normalised o = %r" % (o_norm_trace))
    assert np.all(np.isclose(o_norm_trace, 1, rtol=1e-10))

@given(d = st.integers(min_value=1, max_value=16))
def test_reciprocal_operator(d):
    o = random_operator(d)
    o_r = o**(-1)
    note("o = %r" % (o.matrix))
    note("o_r = %r" % (o_r.matrix))
    assert np.all(np.isclose((o*o_r).matrix, np.identity(d), rtol=1e-10))
    
# Checks the fact that the eigenvalues of the exponential of an Operator o are the exponentials of
# o's eigenvalues
@given(d = st.integers(min_value=1, max_value=8))
def test_exponential_operator_eigenvalues(d):
    o = random_operator(d)
    o_e = o.diagonalisation()[0]
    exp_e = o.exp().diagonalisation()[0]
    sorted_exp_o_e = np.sort(np.exp(o_e))
    sorted_exp_e = np.sort(exp_e)
    note("o = %r" % (o.matrix))
    note("exp(o) = %r" % (o.exp().matrix))
    note("Eigenvalues of o = %r" % (np.sort(o_e)))
    note("Exponential of the eigenvalues of o = %r" % (sorted_exp_o_e))
    note("Eigenvalues of exp(o) = %r" % (sorted_exp_e))
    assert np.all(np.isclose(sorted_exp_o_e, sorted_exp_e, rtol=1e-10))
    
@given(d = st.integers(min_value=1, max_value=16))
def test_observable_real_eigenvalues(d):
    o = random_observable(d)
    eig = o.diagonalisation()[0]
    note("Eigenvalues of o = %r" % (eig))
    assert np.all(np.absolute(np.imag(eig)) < 1e-10)

@given(d = st.integers(min_value=1, max_value=8))
def test_diagonalising_change_of_basis(d):
    o = random_operator(d)
    o_e, p = o.diagonalisation()
    o_sim = o.sim_trans(p).matrix
    o_diag = np.diag(o_e)
    note("o = %r" % (o.matrix))
    note("o (diagonalised through the sim_trans method) = %r" % (o_sim))
    note("o (expressed in diagonal form through direct computation of the eigenvalues) = %r"
         % (o_diag))
    note("Eigenvalues of o = %r" % (o_e))
    assert np.all(np.isclose(o_sim, o_diag, rtol=1e-10))

@given(d = st.integers(min_value=1, max_value=16))
def test_trace_invariance_under_similarity(d):
    o = random_operator(d)
    singularity = True
    while(singularity):
        p = random_operator(d)
        try:
            o_sim = o.sim_trans(p)
            singularity = False
        except LinAlgError:
            pass
    diff = np.absolute(o.trace()-o_sim.trace())
    note("o = %r" % (o.matrix))
    note("p^{-1}op = %r" % (o_sim.matrix))
    note("Trace of o = %r" % (o.trace()))
    note("Trace of p^{-1}op = %r" % (o_sim.trace()))
    note("diff = %r" % (diff))
    assert diff < 1e-10

# Checks that the adjoint of an Operator o's exponential is the exponential of the adjoint of o
@given(d = st.integers(min_value=1, max_value=16))
def test_adjoint_exponential(d):
    o = random_operator(d)
    o_exp = o.exp()
    left_hand_side = (o_exp.dagger()).matrix
    right_hand_side = ((o.dagger()).exp()).matrix
    note("(exp(o))+ = %r" % (left_hand_side))
    note("exp(o+) = %r" % (right_hand_side))    
    assert np.all(np.isclose(left_hand_side, right_hand_side, rtol=1e-10))
    
# Checks that the inverse of the exponential of an Operator o is the same as the exponential of an
# operator o changed by sign
@given(d = st.integers(min_value=1, max_value=4))
def test_inverse_exponential(d):
    o = random_operator(d)
    o_exp = o.exp()
    left_hand_side = (o_exp**(-1)).matrix
    right_hand_side = ((-o).exp()).matrix
    note("(exp(o))^(-1) = %r" % (left_hand_side))
    note("exp(-o) = %r" % (right_hand_side))    
    assert np.all(np.isclose(left_hand_side, right_hand_side, rtol=1e-2))

@given(d = st.integers(min_value=1, max_value=4))
def test_reversibility_change_picture(d):
    o = random_operator(d)
    h = random_operator(d)
    o_ip = o.changed_picture(h, 1, invert=False)
    o1 = o_ip.changed_picture(h, 1, invert=True)
    note("o = %r" % (o.matrix))
    note("o in the changed picture = %r" % (o_ip.matrix))
    note("o brought back from the changed picture = %r" % (o1.matrix))
    assert np.all(np.isclose(o.matrix, o1.matrix, rtol=1))

def test_dmatrix_initialisation_non_hermitian():
    wrong_input = np.array([[1, 1], [0, 0]])
    try:
        dm = Density_Matrix(wrong_input)
        raise AssertionError
    except ValueError:
        pass
    except AssertionError:
        raise AssertionError("No ValueError raised by the initialisation of a Density_Matrix with a non-hermitian square array")

def test_dmatrix_initialisation_non_unit_trace():
    wrong_input = np.array([[1, 0], [0, 1]])
    try:
        dm = Density_Matrix(wrong_input)
        raise AssertionError
    except ValueError:
        pass
    except AssertionError:
        raise AssertionError("No ValueError raised by the initialisation of a Density_Matrix with a square array with trace different from 1")

def test_dmatrix_initialisation_not_positive():
    wrong_input = np.array([[2, 0], [0, -1]])
    try:
        dm = Density_Matrix(wrong_input)
        raise AssertionError
    except ValueError:
        pass
    except AssertionError:
        raise AssertionError("No ValueError raised by the initialisation of a Density_Matrix with a square array which is not positive")

# Checks that the method Density_Matrix.free_evolution conserves the defining properties of the Density_Matrix, i.e. it returns a valid Density_Matrix object.
@given(d = st.integers(min_value=1, max_value=8))
def test_free_evolution_conserves_dm_properties(d):
    dm = random_density_matrix(d)
    h = random_observable(d)
    try:
        evolved_dm = dm.free_evolution(h, 4)
    except ValueError as ve:
        if "The input array lacks the following properties: \n" in ve.args[0]:
            error_message = ve.args[0][49:]
            error_message = "The evolved Density_Matrix lacks the following properties: \n" + error_message
            note("Initial Density_Matrix = %r" % (dm.matrix))
            note("Hamiltonian = %r" % (h.matrix))
            raise AssertionError(error_message)

# Checks that the algorithm used in function random_observable to initialise an Observable object 
# actually yields a hermitian operator
@given(d = st.integers(min_value=1, max_value=16))
def test_random_observable(d):
    try:
        ob_random = random_observable(d)
    except ValueError as ve:
        if "The input array is not hermitian" in ve.args[0]:
            note("Operator returned by random_observable = %r" % (ob_random.matrix))
            raise AssertionError("random_observable fails in the creation of hermitian matrices")

# Checks that the Operator returned by the function random_density_matrix is actually a Density_Matrix
@given(d = st.integers(min_value=1, max_value=16))
def test_random_density_matrix(d):
    try:
        dm_random = random_density_matrix(d)
    except ValueError as ve:
        if "The input array lacks the following properties: \n" in ve.args[0]:
            error_message = ve.args[0][49:]
            error_message = "The generated random Density_Matrix lacks the following properties: \n" + error_message
            raise AssertionError(error_message)

# Checks that the space of density matrices is a convex space, i.e. that the linear combination
# a*dm1 + b*dm2
# where dm1, dm2 are density matrices, a and b real numbers, is a density matrix iff
# a, b in [0, 1] and a + b = 1
@given(d = st.integers(min_value=1, max_value=16))
def test_Convexity_Density_Matrix_Space(d):
    dm1 = random_density_matrix(d)
    dm2 = random_density_matrix(d)
    a = np.random.random()
    b = 1-a
    hyp_dm = a*dm1 + b*dm2
    try:
        hyp_dm.cast_to_density_matrix()
    except ValueError as ve:
        if "The input array lacks the following properties: \n" in ve.args[0]:
            error_message = ve.args[0][49:]
            error_message = "The linear combination a*dm1 + (1-a)*dm2, a in [0, 1.), lacks the following properties: \n" + error_message
            raise AssertionError(error_message)
    not_dm = dm1 + dm2
    try:
        not_dm.cast_to_density_matrix()
        raise AssertionError
    except ValueError:
        pass
    except AssertionError:
        raise AssertionError("No ValueError raised when trying to cast the sum of two Density_Matrix object to Density_Matrix")

# Checks that the evolution is linear, meaning that the evolution of a linear combination of two density matrices through a time t is the linear combination of the evolution of each of them through the same time interval.
@given(d = st.integers(min_value=1, max_value=16))
def test_Linearity_Evolution(d):
    dm1 = random_density_matrix(d)
    dm2 = random_density_matrix(d)
    h = random_observable(d)
    dm_sum = 0.5*(dm1+dm2)
    evolved_dm_sum = dm_sum.free_evolution(h, 5)
    evolved_dm1 = dm1.free_evolution(h, 5)
    evolved_dm2 = dm2.free_evolution(h, 5)
    left_hand_side = evolved_dm_sum.matrix
    right_hand_side = (0.5*(evolved_dm1+evolved_dm2)).matrix
    note("dm1 = %r" % (dm1.matrix))
    note("dm2 = %r" % (dm2.matrix))
    note("Evolved dm1+dm2 = %r" % (left_hand_side))
    note("Evolved dm1 + evolved dm2 = %r" % (right_hand_side))
    assert np.all(np.isclose(left_hand_side, right_hand_side, rtol=1e-10))

# Checks that the constructor of the class Observable raises error when it is initialised with a square array which is not hermitian
def test_Observable_Initialisation_Not_Hermitian():
    wrong_input = np.array([[1, 1], [0, 0]])
    try:
        dm = Observable(wrong_input)
        raise AssertionError
    except ValueError:
        pass
    except AssertionError:
        raise AssertionError("No ValueError raised by the initialisation of an Observable object with a square array which is not hermitian")

# Checks that the expectation values of an Observable are always a real numbers
@given(d = st.integers(min_value=1, max_value=16))
def test_Real_Expectation_Values(d):
    dm = random_density_matrix(d)
    ob = random_observable(d)
    exp_val = ob.expectation_value(dm)
    assert np.imag(exp_val) == 0
    
# Checks the well-known relation
# <(O-<O>)^2> = <O^2> - <O>^2
# where O is an observable, and the angular brackets indicate the expectation value over some state
@given(d = st.integers(min_value=1, max_value=16))
def test_Variance_Formula(d):
    ob = random_observable(d)
    i = Observable(d)
    dm = random_density_matrix(d)
    ob_ev = ob.expectation_value(dm)
    sq_dev = (ob - ob_ev*i)**2
    left_hand_side = sq_dev.expectation_value(dm)
    right_hand_side = (ob**2).expectation_value(dm)-ob_ev**2
    assert np.all(np.isclose(left_hand_side, right_hand_side, 1e-10))

# Generic function which takes a single parameter and returns Observable objects
def Observable_Function(x):
    matrix = np.array([[x, 1+1j*x**2],[1-1j*x**2, x**3]])
    o = Observable(matrix)
    return o

# Checks that the function Magnus_Expansion_1st_Term returns an anti-hermitian operator as expected
def test_AntiHermitianity_Magnus_1st():
    times, time_step = np.linspace(0, 20, num=2001, retstep=True)
    Hamiltonian = np.vectorize(Observable_Function)
    hamiltonian = Hamiltonian(times)
    magnus_1st = Magnus_Expansion_1st_Term(hamiltonian, time_step)
    magnus_1st_dagger = magnus_1st.dagger()
    assert np.all(np.isclose(magnus_1st_dagger.matrix, -magnus_1st.matrix, 1e-10))

# Checks that the function Magnus_Expansion_2nd_Term returns an anti-hermitian operator as expected
def test_AntiHermitianity_Magnus_2nd():
    times, time_step = np.linspace(0, 5, num=501, retstep=True)
    Hamiltonian = np.vectorize(Observable_Function)
    hamiltonian = Hamiltonian(times)
    magnus_2nd = Magnus_Expansion_2nd_Term(hamiltonian, time_step)
    magnus_2nd_dagger = magnus_2nd.dagger()
    assert np.all(np.isclose(magnus_2nd_dagger.matrix, -magnus_2nd.matrix, 1e-10))
    
# Checks that the canonical density matrix computed with the function Canonical_Density_Matrix reduces
# to (1 - hbar*H_0/(k_B*T))/Z when the temperature T gets very large
@given(d = st.integers(min_value=1, max_value=16))
def test_Canonical_Density_Matrix_Large_T_Approximation(d):
    h0 = random_observable(d)
    can_dm = Canonical_Density_Matrix(h0, 300)
    exp = -(Planck*h0*1e6)/(Boltzmann*300)
    num = exp.exp()
    can_p_f = num.trace()   
    can_dm_apx = (Operator(d)+exp)/can_p_f
    assert np.all(np.isclose(can_dm.matrix, can_dm_apx.matrix, rtol=1e-10))







