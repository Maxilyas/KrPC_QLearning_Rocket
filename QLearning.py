import krpc
import random
import time
import sys
import numpy as np
import math
import Classes
import Parameters

# Function for connecting to the server
def connectToServ():
    # Connect to server
    conn = krpc.connect(name='GOPOTATOE')
    conn.space_center.save('launch')
    # Connect to vessels
    vessel = conn.space_center.active_vessel
    return conn, vessel

# parameters for launching the rocket
def setUpRocketLaunch(vessel):
    vessel.control.throttle = 1.0
    time.sleep(1)
    vessel.control.activate_next_stage()
    #vessel.control.sas = True

# Choose one action
def chooseRandomA(vessel, a):
    if a == 0:
        Classes.Actions.haut(vessel)
    if a == 1:
        Classes.Actions.bas(vessel)
    if a == 2:
        Classes.Actions.gauche(vessel)
    if a == 3:
        Classes.Actions.droite(vessel)
    if a == 4:
        Classes.Actions.nothing(vessel)
    if a == 5:
        Classes.Actions.next(vessel)

def chooseA(Q_table,state):
    # Q_table[state].argmax(Q_table[state])
    print('State :', state)
    for i in range(0,6):
        print('action weights :',Q_table[state][i])
    sys.stdout.flush()
    # Get the maximum value of all actions in one state
    res = np.argwhere(Q_table[state] == np.amax(Q_table[state]))
    # If we get multiple values equals then we choose one randomly
    randA = random.randint(0,len(res)-1)
    #res = Q_table[state].argmax()
    # Returning the index of the value previously determined
    return res[randA][0]

def restartLaunch(conn):
    # Reload the game
    conn.space_center.load('launch')

# Function telling if we need to restart
def isRestartNeed(altitude, altitude_prev, pitch):
    if altitude() < altitude_prev:
        return True
    elif pitch() < 0:
        return True
    else:
        return False
    return False

# Function telling if we actually need to decouple
def isDecplNeeded(fuel):
    cur_fuel = Parameters.getInfoAmountFuel(vessel)
    if fuel - cur_fuel < 720:
        return True
    else:
        return False

#best action a in state s in order to maximize a cumulative reward
def reward(old_state,next_state,fuel):

    if (pitch()/90)*climbRate*2 > climbRate:
        return 1
    else:
        return -1

# take max of all states ( NOT USED )
def max_state(states):
    state_max = 0
    for etat in states:
        if etat.altitude() > state_max:
            state_max = etat.altitude()
    return state_max

# Check in which states the rocket is
def check_next_state(next_state,altitude):
    # Between 0 and 1000 is state 1
    if altitude() <= 1000.0:
        next_state.v_state = 0
        return next_state
    # Between 1000 and 5000 is state 2
    elif altitude() > 1000.0 and altitude() <= 5000.0:
        next_state.v_state = 1
        return next_state
    # Between 5000 and 20000 is state 3
    elif altitude() > 5000.0 and altitude() <= 20000.0:
        next_state.v_state = 2
        return next_state
    # Between 20000 and 50000 is state 4
    elif altitude() > 20000.0 and altitude() <= 50000.0:
        next_state.v_state = 3
        return next_state
    # Between 50000 and 100000 is state 5
    elif altitude() > 50000.0 and altitude() <= 100000.0:
        next_state.v_state = 4
        return next_state
    else:
        print('OMG plus de 100 0000 ?')
        next_state.v_state = 4
        return next_state

if __name__ == "__main__":
    # Connect to serv via krpc.connect
    conn, vessel = connectToServ()
    # nb flight done
    nb_flight_count = [0,0,0,0,0]
    # get orbital and surface referential frame
    obt_frame, srf_frame = Parameters.getOrbSrfFrame(vessel)
    # set variables for checking parameters
    altitude_launch = Parameters.getMeanAltitude(vessel)
    fuel = Parameters.getInfoMaxFuel(vessel)

    # variables for all the telemetry needed
    altitude, velocity, pitch, heading, roll = Parameters.Telemetry(conn, vessel)
    # init Qvalues : epsilon,gamma,alpha
    Qvalues = Classes.QValues()
    epsilon = Qvalues.epsilon
    # nb of actions
    nbacts = 6
    # Orbital, surface and climbing speed
    obt_speed = Parameters.obtSpeed(vessel,obt_frame)
    srf_speed = Parameters.srfSpeed(vessel,srf_frame)
    climbRate = Parameters.climbingSpeed(vessel,srf_frame)
    print('#############TELEMETRY###############')
    print('ALTITUDE is :', altitude())
    print('DV is :', velocity())
    print('PITCH is :', pitch())
    print('HEADING is :', heading())
    print('ROLL is :', roll())
    print('########END_OF_COMMUNICATION#########')
    sys.stdout.flush()

    # 5 states depending on altitude / 6 actions Z,S,Q,D,N,Decpl
    # init Q_table with zeros
    Q_table = np.zeros((5, 6))
    # create two states
    state = Classes.State(altitude, velocity, pitch, heading, roll)
    next_state = Classes.State(altitude, velocity, pitch, heading, roll)

    while True:
        # Set up throttle,sas,detached clamp
        setUpRocketLaunch(vessel)
        altitude_prevA = Parameters.getMeanAltitude(vessel)
        #epsilon = QValues.initE(Qvalues)
        #state = State(speed, altitude, pitch, heading, roll)
        for i in range(5000):
            print("nb_flight_count EQUALS :",nb_flight_count)
            if random.randint(0, 100) > epsilon * 100:
                print('ACTION PRIS EN FONCTION DES QVALUES ! EPSILON : ', epsilon)
                try:
                    dv = Parameters.deltaV(vessel,conn)
                    srf_speed = Parameters.srfSpeed(vessel,srf_frame)
                    climbRate = Parameters.climbingSpeed(vessel,srf_frame)
                except:
                    print("Gros ton vaisseau a explosé, fait gaffe")
                    nb_flight_count[state.v_state] = nb_flight_count[state.v_state] + 1
                    restartLaunch(conn)
                print('Surface speed = %.1f m/s' % srf_speed)
                print('CLIMB RATE :',climbRate)
                # Altitude before X actions
                altitude_prevA = Parameters.updateAltitudePrevA(vessel, i, altitude_prevA)
                # Downsizing epsilon
                if nb_flight_count[state.v_state] > 10:
                    epsilon = Qvalues.updateE(epsilon)
                # Choosing the best action possible in the current state
                a = chooseA(Q_table,state.v_state)
                # Choosing the action which correspond to the variable a
                chooseRandomA(vessel,a)
                # One action is 1s in time
                time.sleep(1.0)
                # Looking for the next_state
                next_state = check_next_state(next_state,altitude)
                # Choosing the best action possible for the next state
                next_a = chooseA(Q_table,next_state.v_state)
                # Updating Q_table (Bellman equation)
                Q_table[state.v_state][a] = (1-Qvalues.alpha)*Q_table[state.v_state][a] + Qvalues.alpha*(reward(state, next_state, fuel) + Qvalues.gamma*Q_table[next_state.v_state][next_a])
                # Next state become current state
                state = next_state
                # Updating fuel remaining
                fuel = Parameters.getInfoAmountFuel(vessel)
                # Looking if we have to restart the game
                if isRestartNeed(altitude, altitude_prevA, pitch):
                    nb_flight_count[state.v_state] = nb_flight_count[state.v_state] +1
                    restartLaunch(conn)
                    break
            else:
                print('ACTION RANDOM')
                print('EPSILON : ', epsilon)
                try:
                    dv = Parameters.deltaV(vessel,conn)
                    srf_speed = Parameters.srfSpeed(vessel,srf_frame)
                    climbRate = Parameters.climbingSpeed(vessel,srf_frame)
                except:
                    print("Gros ton vaisseau a explosé, fait gaffe")
                    nb_flight_count[state.v_state] = nb_flight_count[state.v_state] + 1
                    restartLaunch(conn)

                print('Surface speed = %.1f m/s' % srf_speed)
                print('CLIMB RATE :', climbRate)
                # Altitude before X actions
                altitude_prevA = Parameters.updateAltitudePrevA(vessel, i, altitude_prevA)
                # Choosing a random number (nbacts of actions available)
                a = random.randint(0, nbacts - 1)
                # Choosing the action which correspond to the variable a
                chooseRandomA(vessel,a)
                # One action is 1s in time
                time.sleep(1.0)
                # Looking for the next_state
                next_state = check_next_state(next_state, altitude)
                # Choosing the best action possible for the next state
                next_a = chooseA(Q_table, next_state.v_state)
                # Updating Q_table (Bellman equation)
                Q_table[state.v_state][a] = (1 - Qvalues.alpha) * Q_table[state.v_state][a] + Qvalues.alpha * (reward(state, next_state, fuel) + Qvalues.gamma * Q_table[next_state.v_state][next_a])
                # Next state become current state
                state = next_state
                # Downsizing epsilon
                if nb_flight_count[state.v_state] > 10:
                    epsilon = Qvalues.updateE(epsilon)
                # Updating fuel remaining
                fuel = Parameters.getInfoAmountFuel(vessel)
                # Looking if we have to restart the game
                if isRestartNeed(altitude, altitude_prevA, pitch):
                    nb_flight_count[state.v_state] = nb_flight_count[state.v_state] + 1
                    restartLaunch(conn)
                    break
