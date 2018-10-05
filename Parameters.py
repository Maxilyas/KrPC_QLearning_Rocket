import krpc
import random
import time
import sys
import numpy as np
import math

# Get referential for orbital and surface
def getOrbSrfFrame(vessel):
    obt_frame = vessel.orbit.body.non_rotating_reference_frame
    srf_frame = vessel.orbit.body.reference_frame
    return obt_frame, srf_frame

# Telemetry
def Telemetry(conn, vessel):
    altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    velocity = conn.add_stream(getattr, vessel.flight(), 'velocity')
    pitch = conn.add_stream(getattr, vessel.flight(), 'pitch')
    heading = conn.add_stream(getattr, vessel.flight(), 'heading')
    roll = conn.add_stream(getattr, vessel.flight(), 'roll')
    return altitude, velocity, pitch, heading, roll

# Return the max fuel capacity of the vessel
def getInfoMaxFuel(vessel):
    return vessel.resources.max('LiquidFuel')
# Return the amount of fuel remaining
def getInfoAmountFuel(vessel):
    return vessel.resources.amount('LiquidFuel')
# Return mean_altitude
def getMeanAltitude(vessel):
    return vessel.flight().mean_altitude
# Update altitude_prevA after 5 actions
def updateAltitudePrevA(vessel,i, altitude_prevA):
    if i % 5 == 4:
        print('MEAN ALTITUDE',vessel.flight().mean_altitude)
        print ('altitude')
        return getMeanAltitude(vessel)
    return altitude_prevA

# DeltaV of the rocket.
def deltaV(vessel,conn):
    # Mass without resources
    me = conn.add_stream(getattr, vessel, 'dry_mass')
    print('MEmpty =', me())
    # Mass final
    mf = conn.add_stream(getattr, vessel, 'mass')
    print('total mass =', mf())
    # Mass propellant
    mp = mf() - me()
    print('MPropellant =', mp)
    # Propellant mass ratio
    try:
        MR = mf()/me()
    except ZeroDivisionError:
        print("You've explode (Paramaters>deltaV>me())")
    print('Propellant mass ratio =', MR)
    # Specific impulse :  how effectively a rocket uses propellant or jet engine uses fuel.
    Isp = conn.add_stream(getattr, vessel, 'specific_impulse')
    print('ISP : ', Isp())
    # Gravity
    g0 = 9.81
    # return deltaV
    return Isp()*g0*math.log(MR)

# NOT FINISH
def velocity(vessel,conn):
    ref_frame = conn.space_center.ReferenceFrame.create_hybrid(
        position=vessel.orbit.body.reference_frame,
        rotation=vessel.surface_reference_frame)

    # Thrust
    T = conn.add_stream(getattr, vessel, 'thrust')
    # density
    p = conn.add_stream(getattr,vessel,'atmosphere_pressure')
    # mass
    m = conn.add_stream(getattr, vessel, 'mass')
    # The total aerodynamic forces acting on the vessel
    A = conn.add_stream(getattr,vessel.flight(),'aerodynamic_force')
    # The dynamic pressure acting on the vessel
    q = conn.add_stream(getattr,vessel.flight(),'dynamic_pressure')
    # The drag
    D = conn.add_stream(getattr,vessel.flight(),'drag')
    # velocity of the vessel
    v = vessel.flight(ref_frame).velocity
    # The coefficient of drag
    Cd = D / (q * A)
    # G force
    g = conn.add_stream(getattr,conn.space_center,'g')
    dv_dt = (T -(1/2*Cd*A()*math.sqrt(v())) - (m*g()*math.sin()))/ m

# Orbital speed in orbital referential
def obtSpeed(vessel,obt_frame):
        return vessel.flight(obt_frame).speed
# Surface speed in surface referential
def srfSpeed(vessel,srf_frame):
        return vessel.flight(srf_frame).speed
# Climbing speed in surface referential
def climbingSpeed(vessel,srf_frame):
        return vessel.flight(srf_frame).vertical_speed
